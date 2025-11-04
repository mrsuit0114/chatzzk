from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.data_access.repositories.logics.vod_base import VODLogicBase
from chatzzk.packages.schemas.dto.repo_params.chzzk.vod import ChzzkVODCreateParams
from chatzzk.packages.schemas.orm.models import VOD, ChzzkVOD, VODOverallProcessingStatus, VODProcessingStatusDetail


class ChzzkVODLogic(VODLogicBase):
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
