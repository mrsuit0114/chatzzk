from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from chatzzk.packages.constants.service_codes import PlatformCode, VODProcessingStep, VODProcessingStepStatus
from chatzzk.packages.data_access.repositories.logics.vod_base import VODLogicBase
from chatzzk.packages.schemas.dto.repo_params.core.vod import VODCreateParams, VODFindParams
from chatzzk.packages.schemas.orm.models import VOD, VODProcessingStatusDetail


class VODRepository:
    def __init__(self, vod_logic_factory: dict[PlatformCode, VODLogicBase]):
        self.factory = vod_logic_factory

    def _get_logic(self, platform_code: PlatformCode):
        logic_module = self.factory.get(platform_code)
        if logic_module:
            return logic_module
        else:
            raise ValueError(f"No logic module found for platform_code: {platform_code}")

    def create_platform_vod(self, session: AsyncSession, platform_code: PlatformCode, params: VODCreateParams) -> VOD:
        logic_module = self._get_logic(platform_code)
        return logic_module.create_platform_vod(session, params)

    async def find_vod_with_platform_vod(
        self, session: AsyncSession, platform_code: PlatformCode, params: VODFindParams
    ) -> VOD:
        logic_module = self._get_logic(platform_code)
        return await logic_module.find_vod_with_platform_vod(session, params)

    async def find_vod_with_processing_detail_by_id(self, session: AsyncSession, vod_id: int) -> VOD | None:
        stmt = select(VOD).options(joinedload(VOD.vod_processing_status_detail)).where(VOD.id == vod_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    def update_processing_detail(
        self,
        session: AsyncSession,
        vod: VOD,
        *,
        step: VODProcessingStep,
        status: VODProcessingStepStatus,
        start_time: datetime,
        end_time: datetime,
    ) -> VODProcessingStatusDetail:
        vod_processing_status_detail = vod.vod_processing_status_detail
        status_details = vod_processing_status_detail.status_details
        status_details[step] = {
            "status": status,
            "start_time": start_time.isoformat() if isinstance(start_time, datetime) else start_time,
            "end_time": end_time.isoformat() if isinstance(end_time, datetime) else end_time,
        }
        vod_processing_status_detail.status_details = status_details
        session.add(vod_processing_status_detail)

        return vod_processing_status_detail
