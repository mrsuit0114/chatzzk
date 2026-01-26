from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_core.constants import VODPipelineStatus
from chatzzk_core.schemas.internal.dto import VODDTO, ChannelDTO, PlatformDTO, TargetVODInfo
from chatzzk_data_access.repositories import VODRepository


class VODDispatchService:
    def __init__(
        self,
        vod_repo: VODRepository,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        self.vod_repo = vod_repo
        self.db_session_factory = db_session_factory

    async def allocate_next_batch(self, batch_size: int) -> list[TargetVODInfo]:
        """
        [작업 할당]
        PENDING 상태인 VOD를 batch_size만큼 가져와서 - publish_date asc - 오래된 순
        PROCESSING 상태로 변경한 후, 해당 VOD, channel, platform를 반환합니다.
        """
        target_vod_info = []

        async with self.db_session_factory() as session:
            async with session.begin():
                pending_vods = await self.vod_repo.get_vod_by_status(
                    session, VODPipelineStatus.PENDING, limit=batch_size
                )

                if not pending_vods:
                    return []

                for vod in pending_vods:
                    target_vod_info.append(
                        TargetVODInfo(
                            vod=VODDTO.from_orm(vod),
                            channel=ChannelDTO.from_orm(vod.channel),
                            platform=PlatformDTO.from_orm(vod.channel.platform),
                        )
                    )

                for vod in pending_vods:
                    vod.pipeline_status = VODPipelineStatus.PROCESSING

        return target_vod_info

    async def get_target_vod(self, vod_id: int) -> TargetVODInfo | None:
        async with self.db_session_factory() as session:
            async with session.begin():
                # 1. VOD 조회 (상태 무관하게 가져오거나, 로직에 따라 제한 가능)
                vod = await self.vod_repo.get_by_id(session, vod_id)

                if not vod:
                    return None

                # 2. 상태를 PROCESSING으로 변경 (중복 실행 방지 및 상태 표시)
                vod.pipeline_status = VODPipelineStatus.PROCESSING

                # 3. DTO 변환 및 반환
                return TargetVODInfo(
                    vod=VODDTO.from_orm(vod),
                    channel=ChannelDTO.from_orm(vod.channel),
                    platform=PlatformDTO.from_orm(vod.channel.platform),
                )

    async def allocate_failed_batch(self, batch_size: int) -> list[TargetVODInfo]:
        """
        [작업 할당]
        FAILED 상태인 VOD를 batch_size만큼 가져와서 - publish_date asc - 오래된 순
        PROCESSING 상태로 변경한 후, 해당 VOD, channel, platform를 반환합니다.
        """
        target_vod_info = []

        async with self.db_session_factory() as session:
            async with session.begin():
                failed_vods = await self.vod_repo.get_vod_by_status(session, VODPipelineStatus.FAILED, limit=batch_size)

                if not failed_vods:
                    return []

                for vod in failed_vods:
                    target_vod_info.append(
                        TargetVODInfo(
                            vod=VODDTO.from_orm(vod),
                            channel=ChannelDTO.from_orm(vod.channel),
                            platform=PlatformDTO.from_orm(vod.channel.platform),
                        )
                    )

                for vod in failed_vods:
                    vod.pipeline_status = VODPipelineStatus.PROCESSING

        return target_vod_info

    async def mark_stale_processing_vods_as_failed(self, threshold_minutes: int) -> list[int]:
        """
        [좀비 청소]
        PROCESSING 상태이면서 threshold_minutes 이상 업데이트가 없는 VOD를 FAILED로 변경
        """
        processed_ids = []

        # UTC 기준 시간 계산 (DB가 UTC를 쓴다고 가정)
        limit_time = datetime.now(UTC) - timedelta(minutes=threshold_minutes)

        async with self.db_session_factory() as session:
            async with session.begin():
                # 1. 좀비 VOD 조회 (Repo 메서드 호출)
                stale_vods = await self.vod_repo.get_stale_processing_vods(
                    session, threshold_time=limit_time, limit=100
                )

                if not stale_vods:
                    return []

                # 2. 상태 변경 (FAILED)
                for vod in stale_vods:
                    vod.pipeline_status = VODPipelineStatus.FAILED
                    vod.failure_reason = f"Zombie Detected: No update for {threshold_minutes} min"

                    processed_ids.append(vod.id)

        # 처리된 ID 목록 반환 (로깅용)
        return processed_ids
