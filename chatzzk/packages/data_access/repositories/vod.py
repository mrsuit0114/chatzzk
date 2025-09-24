from typing import Any

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from chatzzk.packages.constants.service_codes import PIPELINE_STATUS_KEY, PipelineStep, StepStatus, VodProcessStatus
from chatzzk.packages.schemas.db_models import ChzzkChannelORM, ChzzkVodORM


class VodRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, channel: ChzzkChannelORM, vod_data: dict) -> ChzzkVodORM | None:
        """
        새로운 VOD 정보를 DB에 생성합니다. 초기 상태는 자동으로 'PENDING'으로 설정됩니다.
        """
        video_no = vod_data.get("video_no")
        try:
            db_vod = ChzzkVodORM(
                channel_pk=channel.id,
                **vod_data,
            )
            self.db.add(db_vod)
            self.db.commit()
            self.db.refresh(db_vod)
            logger.success(f"✅ Created VOD for video_no: {video_no}")
            return db_vod
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create VOD for video_no {video_no}: {e}")
            raise

    def get_by_video_no(self, video_no: str) -> ChzzkVodORM | None:
        """video_no를 사용하여 VOD 정보를 조회합니다."""
        return self.db.query(ChzzkVodORM).filter(ChzzkVodORM.video_no == video_no).first()

    def get_by_pk(self, pk: int) -> ChzzkVodORM | None:
        """기본 키(PK)를 사용하여 VOD 정보를 조회합니다."""
        return self.db.get(ChzzkVodORM, pk)

    def get_list_to_process(self, limit: int = 10) -> list[ChzzkVodORM]:
        """처리가 필요하거나 실패한 VOD 목록을 가져옵니다."""
        return (
            self.db.query(ChzzkVodORM)
            .filter(ChzzkVodORM.process_status.in_([VodProcessStatus.PENDING, VodProcessStatus.FAILED]))
            .limit(limit)
            .all()
        )

    def update_pipeline_step(
        self, vod: ChzzkVodORM, step_name: PipelineStep, status: StepStatus, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        VOD의 status_details(JSONB) 필드 내 특정 파이프라인 단계의 상태를 업데이트합니다.
        """
        try:
            vod.status_details = vod.status_details or {}
            step_update = {PIPELINE_STATUS_KEY: status}
            if metadata:
                step_update.update(metadata)
            vod.status_details[step_name] = step_update
            flag_modified(vod, "status_details")
            self.db.commit()
            logger.info(f"Updated pipeline step '{step_name}' to '{status}' for video_no: {vod.video_no}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update pipeline step for video_no {vod.video_no}: {e}")
            raise

    def update_process_status(self, vod: ChzzkVodORM, status: VodProcessStatus) -> bool:
        """VOD의 전체적인 process_status를 업데이트합니다."""
        try:
            vod.process_status = status
            if status in [VodProcessStatus.COMPLETED, VodProcessStatus.FAILED]:
                vod.processed_at = func.now()
            self.db.commit()
            logger.info(f"Updated overall status to '{status}' for video_no: {vod.video_no}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update overall status for video_no {vod.video_no}: {e}")
            raise
