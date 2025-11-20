from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from chatzzk_data_access.repositories.logics.vod_base import VODLogicBase
from chatzzk_schemas.dto.repo_params.chzzk.vod import ChzzkVODCreateParams, ChzzkVODFindParams
from chatzzk_schemas.orm.models import VOD, ChzzkVOD, VODOverallProcessingStatus, VODProcessingStatusDetail


class ChzzkVODLogic(VODLogicBase):
    def __init__(self, field_map: dict):
        self.field_map = field_map

    def create_platform_vod(self, session: AsyncSession, params: ChzzkVODCreateParams) -> VOD:
        vod = VOD(
            channel_id=params.channel_id,
            chzzk_vod=ChzzkVOD(
                video_no=params.video_no,
                video_title=params.video_title,
                duration=params.duration,
                video_category_value=params.video_category_value,
                publish_date=params.publish_date,
                live_open_date=params.live_open_date,
            ),
            vod_overall_processing_status=VODOverallProcessingStatus(),
            vod_processing_status_detail=VODProcessingStatusDetail(),
        )

        session.add(vod)

        return vod

    async def find_vod_with_platform_vod(self, session: AsyncSession, params: ChzzkVODFindParams) -> VOD:
        filters = []

        for key, value in params.model_dump(exclude_none=True).items():
            column = self.field_map.get(key)
            if column is not None:
                filters.append(column == value)

        stmt = (
            select(VOD)
            .options(joinedload(VOD.chzzk_vod))
            .join(ChzzkVOD, VOD.id == ChzzkVOD.vod_id)
            .where(and_(*filters))
        )

        result = await session.execute(stmt)
        return result.scalars().first()
