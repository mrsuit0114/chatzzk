from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk_core.constants import PlatformCode
from chatzzk_core.schemas.config.services.vod_discovery import ChzzkVODDiscoveryConfig
from chatzzk_core.schemas.external import ChzzkVODMeta
from chatzzk_data_access.repositories.channel import ChannelRepository
from chatzzk_data_access.repositories.vod import VODRepository


class ChzzkVODDiscoveryService:
    # 실제 사용 부분에서 결국 서비스에 대해 알아야하기 때문에 인터페이스가 무의미
    # 인터페이스는 테스팅 환경에서 빛을 발하는데 현재 계획이 없기 때문에 인터페이스는 사용하지 않음
    def __init__(
        self,
        channel_repo: ChannelRepository,
        vod_repo: VODRepository,
        chzzk_api_client: ChzzkAPIClient,
        db_session_factory: async_sessionmaker[AsyncSession],
        config: ChzzkVODDiscoveryConfig,
    ):
        self.channel_repo = channel_repo
        self.vod_repo = vod_repo
        self.chzzk_api_client = chzzk_api_client
        self.db_session_factory = db_session_factory
        self.config = config
        self.platform_code = PlatformCode.CHZZK

    def _is_target_vod(self, vod_meta: ChzzkVODMeta, now_utc: datetime) -> bool:
        cfg = self.config
        if vod_meta.duration < cfg.min_duration_s:
            return False

        if vod_meta.publish_date > now_utc - cfg.min_publish_date_age:
            return False
        # Ture: adult, self.allow_adult - (True, True), (False, True), (False, False) -> 수집
        # Flase: (True, False)
        if vod_meta.adult and not cfg.allow_adult:
            return False

        if vod_meta.live_pv < cfg.live_pv:
            return False

        return True

    async def list_active_channels(self) -> list[dict]:
        # 수집 대상 채널을 반환
        target_channels = []
        async with self.db_session_factory() as session:
            channels = await self.channel_repo.get_active_channels_by_platform_code(session, self.platform_code)

            target_channels = [
                {
                    "channel_id": ch.id,
                    "platform_channel_id": ch.platform_channel_id,
                    "last_vod_crawled_at": ch.last_vod_crawled_at,
                }
                for ch in channels
            ]

        return target_channels

    async def scan_new_vods(self, target_channel: dict) -> tuple[list[ChzzkVODMeta], datetime]:
        # 수집해야할 vod 리스트와 탐색 datetime(utc)를 반환
        platform_channel_id = target_channel["platform_channel_id"]
        last_crawled_at = target_channel["last_vod_crawled_at"]

        now_utc = datetime.now(UTC)

        recent_vods = await self.chzzk_api_client.fetch_recent_vod_metas(
            platform_channel_id, collect_after=last_crawled_at
        )

        filtered_vods = [vod for vod in recent_vods if self._is_target_vod(vod, now_utc)]

        return filtered_vods, now_utc

    async def save_discovery_results(
        self, channel_id: int, vod_metas: list[ChzzkVODMeta], scanned_at: datetime
    ) -> list[int]:
        # vod를 등록하고, channel의 last_vod_crawled_at 업데이트, VODPipelineLog 한번에 트랜잭션
        if not vod_metas:
            async with self.db_session_factory() as session:
                async with session.begin():
                    await self.channel_repo.update_last_crawled_at(session, channel_id, scanned_at)
            return []

        vod_dicts = [
            {
                "channel_id": channel_id,
                "video_no": vod.video_no,
                "video_title": vod.video_title,
                "duration": vod.duration,
                "publish_date": vod.publish_date,
            }
            for vod in vod_metas
        ]

        async with self.db_session_factory() as session:
            async with session.begin():
                created_ids = await self.vod_repo.bulk_insert_if_not_exists(session, vod_dicts)

                if created_ids:
                    log_dicts = [{"vod_id": vod_id} for vod_id in created_ids]
                    await self.vod_repo.bulk_insert_logs(session, log_dicts)

                await self.channel_repo.update_last_crawled_at(session, channel_id, scanned_at)

        return created_ids
