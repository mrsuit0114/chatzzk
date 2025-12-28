from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_core.constants import VODPipelineStatus
from chatzzk_data_access.repositories import VODRepository


class VODDispatchService:
    def __init__(
        self,
        vod_repo: VODRepository,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        self.vod_repo = vod_repo
        self.db_session_factory = db_session_factory

    async def allocate_next_batch(self, batch_size: int = 5) -> list[int]:
        """
        [작업 할당]
        PENDING 상태인 VOD를 batch_size만큼 가져와서
        PROCESSING 상태로 변경한 후, 해당 VOD의 ID 리스트를 반환합니다.

        이 메서드는 원자적(Atomic)으로 동작하여 중복 할당을 방지해야 합니다.
        """
        target_vod_ids = []

        async with self.db_session_factory() as session:
            async with session.begin():
                pending_vods = await self.vod_repo.get_vod_by_status(
                    session, VODPipelineStatus.PENDING, limit=batch_size
                )

                if not pending_vods:
                    return []

                for vod in pending_vods:
                    vod.pipeline_status = VODPipelineStatus.PROCESSING
                    target_vod_ids.append(vod.id)

        return target_vod_ids
