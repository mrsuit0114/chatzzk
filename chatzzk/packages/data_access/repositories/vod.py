from loguru import logger
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from chatzzk.packages.constants.service_codes import VodProcessStatus
from chatzzk.packages.schemas.db_models import (
    ChzzkChannelORM,
    ChzzkVodAnalyticsORM,
    ChzzkVodORM,
    ChzzkVodProcessingStatusORM,
)


class VodRepository:
    """VOD 애그리거트에 대한 모든 데이터베이스 접근을 캡슐화합니다."""

    def __init__(self, db: Session):
        self.db = db

    def create_or_get_vod(self, channel: ChzzkChannelORM, vod_data: dict) -> tuple[ChzzkVodORM, bool]:
        """
        video_no를 기준으로 VOD를 조회하고, 없으면 새로 생성합니다.
        멱등성을 보장하며, 생성 여부를 bool 값으로 함께 반환합니다.
        (VOD, created: bool)
        """
        video_no = vod_data.get("video_no")
        if not video_no:
            raise ValueError("video_no is required")

        # 1. 먼저 VOD가 존재하는지 확인
        existing_vod = self.get_by_video_no(video_no)
        if existing_vod:
            logger.info(f"VOD with video_no {video_no} already exists.")
            return existing_vod, False

        # 2. VOD가 없으면 새로 생성
        try:
            logger.info(f"Creating new VOD for video_no: {video_no}")
            db_vod = ChzzkVodORM(channel_pk=channel.id, **vod_data)
            db_vod.processing_status = ChzzkVodProcessingStatusORM()  # 기본값 PENDING
            db_vod.analytics = ChzzkVodAnalyticsORM()

            self.db.add(db_vod)
            self.db.commit()
            self.db.refresh(db_vod)
            logger.success(f"✅ Created VOD for video_no: {video_no}")
            return db_vod, True
        except IntegrityError:  # 동시 생성 시도 시 UNIQUE 제약조건 위반 오류
            self.db.rollback()
            logger.warning(f"Race condition detected for video_no {video_no}. Re-fetching.")
            # 다른 트랜잭션이 먼저 생성했을 것이므로, 다시 조회하여 반환
            return self.get_by_video_no(video_no), False
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create VOD for video_no {video_no}: {e}")
            raise

    def find_and_lock_pending_vod(self) -> ChzzkVodORM | None:
        """
        처리 대기중인 VOD를 원자적으로 획득(claim)하고, 상태를 PROCESSING으로 변경합니다.
        여러 워커가 경쟁할 때 단 하나의 워커만 작업을 가져가도록 보장합니다.
        """
        try:
            # FOR UPDATE SKIP LOCKED: PENDING 상태인 행을 찾되, 다른 워커가 잠근 행은 건너뜁니다.
            vod = (
                self.db.query(ChzzkVodORM)
                .join(ChzzkVodORM.processing_status)
                .filter(ChzzkVodProcessingStatusORM.process_status == VodProcessStatus.PENDING)
                .order_by(ChzzkVodORM.created_at)
                .with_for_update(skip_locked=True)
                .first()
            )

            if not vod:
                return None

            # VOD를 찾았다면, 즉시 상태를 PROCESSING으로 변경
            vod.processing_status.process_status = VodProcessStatus.PROCESSING
            self.db.commit()
            logger.info(f"Locked VOD for processing: {vod.video_no}")
            return vod
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to find and lock VOD: {e}")
            raise

    def update_pipeline_step_status(self, vod_pk: int, step_name: str, status_data: dict) -> bool:
        """
        JSONB '||' 연산자를 사용하여 status_details 필드를 원자적으로 업데이트합니다.
        이 방법은 여러 서브 작업이 동시에 상태를 기록할 때 발생하는 Race Condition을 방지합니다.
        """
        try:
            update_value = {step_name: status_data}
            result = (
                self.db.query(ChzzkVodProcessingStatusORM)
                .filter(ChzzkVodProcessingStatusORM.vod_pk == vod_pk)
                .update(
                    {
                        ChzzkVodProcessingStatusORM.status_details: func.coalesce(
                            ChzzkVodProcessingStatusORM.status_details, cast({}, JSONB)
                        ).op("||")(cast(update_value, JSONB))
                    },
                    synchronize_session=False,  # 중요: 세션 동기화 비활성화
                )
            )
            if result == 0:
                logger.warning(f"No VOD processing status found for vod_pk {vod_pk} to update.")
                return False

            self.db.commit()
            logger.info(f"Atomically updated pipeline step '{step_name}' for vod_pk: {vod_pk}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to atomically update pipeline step for vod_pk {vod_pk}: {e}")
            raise

    def update_analytics(self, vod_pk: int, analytics_data: dict) -> bool:
        """분석이 완료된 통계 데이터를 chzzk_vod_analytics 테이블에 업데이트합니다."""
        try:
            result = (
                self.db.query(ChzzkVodAnalyticsORM)
                .filter(ChzzkVodAnalyticsORM.vod_pk == vod_pk)
                .update(analytics_data, synchronize_session=False)
            )
            if result == 0:
                logger.warning(f"No VOD analytics found for vod_pk {vod_pk} to update.")
                return False

            self.db.commit()
            logger.success(f"Updated analytics for vod_pk: {vod_pk}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update analytics for vod_pk {vod_pk}: {e}")
            raise

    def update_overall_status(self, vod_pk: int, status: VodProcessStatus) -> bool:
        """VOD의 최종 처리 상태를 업데이트합니다. (예: COMPLETED, FAILED)"""
        try:
            result = (
                self.db.query(ChzzkVodProcessingStatusORM)
                .filter(ChzzkVodProcessingStatusORM.vod_pk == vod_pk)
                .update({"process_status": status}, synchronize_session=False)
            )
            if result == 0:
                logger.warning(f"No VOD processing status found for vod_pk {vod_pk} to update.")
                return False

            self.db.commit()
            logger.info(f"Updated overall status to '{status}' for vod_pk: {vod_pk}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update overall status for vod_pk {vod_pk}: {e}")
            raise

    def get_by_video_no(self, video_no: str) -> ChzzkVodORM | None:
        """video_no를 사용하여 VOD 정보를 조회합니다. 연관된 모든 정보를 Eager Loading합니다."""
        return (
            self.db.query(ChzzkVodORM)
            .options(
                joinedload(ChzzkVodORM.processing_status),
                joinedload(ChzzkVodORM.analytics),
            )
            .filter(ChzzkVodORM.video_no == video_no)
            .first()
        )

    def get_by_pk(self, pk: int) -> ChzzkVodORM | None:
        """기본 키(PK)를 사용하여 VOD 정보를 조회합니다. 연관된 모든 정보를 Eager Loading합니다."""
        return (
            self.db.query(ChzzkVodORM)
            .options(
                joinedload(ChzzkVodORM.processing_status),
                joinedload(ChzzkVodORM.analytics),
            )
            .get(pk)
        )
