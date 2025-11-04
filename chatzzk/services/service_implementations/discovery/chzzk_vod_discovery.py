import asyncio
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.vod import VODRepository
from chatzzk.packages.schemas.clients.chzzk import VODInfo, VODMeta
from chatzzk.packages.schemas.config.discovery import DiscoveryServiceConfig
from chatzzk.packages.schemas.dto.api.chzzk.vod import ChzzkVODRegisterRequestDTO, ChzzkVODRegisterResponseDTO
from chatzzk.packages.schemas.dto.repo_params.chzzk.channel import ChzzkChannelFindParams
from chatzzk.packages.schemas.dto.repo_params.chzzk.vod import ChzzkVODCreateParams
from chatzzk.services.interfaces.vod_discovery import VODDiscoveryInterface


class ChzzkVODDiscoveryService(VODDiscoveryInterface):
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        channel_repo: ChannelRepository,
        vod_repo: VODRepository,
        chzzk_api_client: ChzzkAPIClient,
        config: DiscoveryServiceConfig,
    ):
        self.db_session_factory = db_session_factory
        self.channel_repo = channel_repo
        self.vod_repo = vod_repo
        self.api_client = chzzk_api_client
        self.vod_filter = config.vod_filter
        self.platform_code = PlatformCode.CHZZK

    async def register_vods(self, dto: ChzzkVODRegisterRequestDTO) -> list[ChzzkVODRegisterResponseDTO]:
        logger.info(f"Starting VOD discovery process for channel: {dto.platform_channel_id}")
        responses: list[ChzzkVODRegisterResponseDTO] = []

        async with self.db_session_factory() as session:
            channel_find_params = ChzzkChannelFindParams(platform_channel_id=dto.platform_channel_id)
            channel = await self.channel_repo.find_platform_channel(session, self.platform_code, channel_find_params)
            if not channel:
                raise ValueError(f"Channel '{dto.platform_channel_id}' not found in DB. Please add it first.")
            channel_id = channel.id

        vod_crawled_at = datetime.now(UTC)
        vod_metas_from_api = await self._fetch_vod_metas(dto.platform_channel_id, dto.collect_after_date_utc)
        filtered_vod_metas = self._filter_vod_metas(vod_metas_from_api)

        if not filtered_vod_metas:
            logger.info(f"No new VODs found or passed local filter for channel {dto.platform_channel_id}.")
            return []

        vod_infos = await self._fetch_new_vod_infos(filtered_vod_metas)

        if not vod_infos:
            logger.warning(f"No detailed VOD info could be fetched for channel {dto.platform_channel_id}.")
            return []

        async with self.db_session_factory() as session:
            async with session.begin():  # 모든 VOD 저장을 하나의 트랜잭션으로 묶음
                channel = await self.channel_repo.find_channel_by_id(session, channel_id)
                if not channel:
                    raise ValueError(f"Channel not found: {channel_id}")

                for vod_info in vod_infos:
                    try:
                        # 레포지토리에 전달할 VOD 생성용 파라미터 객체 구성
                        vod_create_params = ChzzkVODCreateParams(
                            channel_id=channel.id,
                            video_no=vod_info.video_no,
                            video_title=vod_info.video_title,
                            duration=vod_info.duration,
                            video_category_value=vod_info.video_category_value,
                            publish_date=vod_info.publish_date,
                            live_open_date=vod_info.live_open_date,
                        )

                        # 레포지토리의 VOD 생성 메서드 호출
                        new_vod = self.vod_repo.create_platform_vod(
                            session, platform_code=self.platform_code, params=vod_create_params
                        )
                        await session.flush()
                        responses.append(
                            ChzzkVODRegisterResponseDTO(video_no=new_vod.chzzk_vod.video_no, status="ADDED")
                        )

                    except IntegrityError:
                        logger.warning(
                            f"VOD '{vod_info.video_no}' already exists for channel {dto.platform_channel_id}. Skipping."
                        )
                        responses.append(ChzzkVODRegisterResponseDTO(video_no=vod_info.video_no, status="EXISTING"))
                    except Exception as e:
                        logger.error(
                            f"Failed to register VOD '{vod_info.video_no}' for channel {dto.platform_channel_id}: {e}"
                        )
                        responses.append(ChzzkVODRegisterResponseDTO(video_no=vod_info.video_no, status="FAILED"))

                self.channel_repo.update_channel(session, channel, last_vod_crawled_at=vod_crawled_at)

        logger.info(f"Finished VOD discovery for channel {dto.platform_channel_id}. Processed {len(vod_infos)} VODs.")
        return responses

    async def _fetch_vod_metas(self, platform_channel_id: str, collect_after_date_utc: datetime) -> list[VODMeta]:
        collect_after_timestamp_ms = int(collect_after_date_utc.timestamp() * 1000) if collect_after_date_utc else None
        vod_meta_generator = self.api_client.fetch_channel_vods(platform_channel_id, collect_after_timestamp_ms)
        return [vod_meta async for vod_meta in vod_meta_generator]

    def _filter_vod_metas(self, vod_metas: list[VODMeta]) -> list[VODMeta]:
        if not vod_metas:
            return []

        cur_timestamp_utc = int(datetime.now(UTC).timestamp() * 1000)

        filtered_vod_metas = [vod for vod in vod_metas if self.vod_filter.is_valid(vod, cur_timestamp_utc)]
        return filtered_vod_metas

    async def _fetch_new_vod_infos(self, filtered_vod_metas: list[VODMeta]) -> list[VODInfo]:
        """
        필터링된 VOD 메타데이터 리스트에 대해 상세 정보를 수집합니다.
        """
        if not filtered_vod_metas:
            return []

        logger.info(f"Fetching details for {len(filtered_vod_metas)} VODs...")

        tasks = [self.api_client.fetch_vod_info(vod_meta.video_no) for vod_meta in filtered_vod_metas]
        vod_info_results = await asyncio.gather(*tasks)

        # None이 아닌 유효한 상세 정보만 필터링
        valid_vod_infos = [info for info in vod_info_results if info]
        if not valid_vod_infos:
            logger.warning("No valid VOD details could be fetched.")
            return []
        return valid_vod_infos
