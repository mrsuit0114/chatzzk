from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_core.constants.service_codes import VODPipelineStepStatus, VODProcessingStep
from chatzzk_data_access.repositories.vod import VODRepository


class BasePipelineService:
    """
    모든 VOD 파이프라인 서비스가 상속받아야 하는 기본 클래스.
    공통적인 DB 상태 확인 및 업데이트 로직을 제공합니다.
    """

    def __init__(
        self,
        vod_repo: VODRepository,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        self.vod_repo = vod_repo
        self.db_session_factory = db_session_factory

    async def is_step_completed(self, vod_id: int, step: VODProcessingStep) -> bool:
        async with self.db_session_factory() as session:
            log_details = await self.vod_repo.get_log_details(session, vod_id)
            step_info = log_details.get(step.value, {})

            if step_info.get("status") == VODPipelineStepStatus.COMPLETED.value:
                return True
            return False

    async def update_step_status(
        self,
        vod_id: int,
        step: VODProcessingStep,
        status: VODPipelineStepStatus,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        update_payload = {
            step.value: {
                "status": status.value,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
            }
        }

        async with self.db_session_factory() as session:
            async with session.begin():
                await self.vod_repo.update_log_details(session, vod_id, update_payload)
