import os
from contextlib import contextmanager
from typing import Any

from loguru import logger
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from chatzzk.packages.constants.service_codes import VodProcessStatus

# 1. ORM 모델 임포트
from chatzzk.packages.schemas.db_models import (
    Base,
    ChzzkAnalysisResultORM,
    ChzzkChannelORM,
    ChzzkVodORM,
)

DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set.")

engine = create_engine(DATABASE_URL, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Session:
    """DB 세션을 안전하게 사용하고 닫기 위한 컨텍스트 매니저."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """DB에 정의된 모든 테이블을 생성합니다. (최초 1회 실행용)"""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.success("Database tables initialized successfully.")


# --- 2. 플랫폼 (platforms) 및 채널 (chzzk_channels) 관리 함수 ---


def get_or_create_channel(db: Session, channel_id: str, channel_name: str) -> ChzzkChannelORM:
    """channel_id로 채널을 조회하고, 없으면 새로 생성합니다."""
    db_channel = db.query(ChzzkChannelORM).filter(ChzzkChannelORM.channel_id == channel_id).first()
    if not db_channel:
        logger.info(f"Channel not found for channel_id: {channel_id}. Creating new one.")
        db_channel = ChzzkChannelORM(channel_id=channel_id, channel_name=channel_name)
        try:
            db.add(db_channel)
            db.commit()
            db.refresh(db_channel)
            logger.success(f"Successfully created channel: {channel_name} ({channel_id})")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create channel {channel_name}: {e}")
            raise
    return db_channel


def get_active_channels(db: Session) -> list[ChzzkChannelORM]:
    """데이터 수집이 활성화된 모든 채널 목록을 반환합니다."""
    return db.query(ChzzkChannelORM).filter(ChzzkChannelORM.is_active).all()


# --- 3. VOD 정보 및 파이프라인 상태 관리 (핵심 리팩토링) ---


def create_vod(db: Session, channel: ChzzkChannelORM, vod_data: dict) -> ChzzkVodORM | None:
    """
    새로운 VOD 정보를 DB에 생성합니다. 초기 상태는 자동으로 'PENDING'으로 설정됩니다.
    """
    video_no = vod_data.get("video_no")
    try:
        # Pydantic 모델이나 dict에서 안전하게 필드 추출
        db_vod = ChzzkVodORM(
            channel_id=channel.id,  # FK는 부모 객체의 id를 사용
            **vod_data,
        )
        db.add(db_vod)
        db.commit()
        db.refresh(db_vod)
        logger.success(f"✅ Created VOD for video_no: {video_no}")
        return db_vod
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create VOD for video_no {video_no}: {e}")
        return None


def get_vod_by_video_no(db: Session, video_no: str) -> ChzzkVodORM | None:
    """video_no를 사용하여 VOD 정보를 조회합니다."""
    return db.query(ChzzkVodORM).filter(ChzzkVodORM.video_no == video_no).first()


def get_vods_to_process(db: Session, limit: int = 10) -> list[ChzzkVodORM]:
    """처리가 필요하거나 실패한 VOD 목록을 가져옵니다."""
    return (
        db.query(ChzzkVodORM)
        .filter(ChzzkVodORM.process_status.in_([VodProcessStatus.PENDING, VodProcessStatus.FAILED]))
        .limit(limit)
        .all()
    )


def update_vod_pipeline_step(
    db: Session, vod: ChzzkVodORM, step_name: str, status: str, metadata: dict[str, Any] | None = None
) -> bool:
    """
    VOD의 status_details(JSONB) 필드 내 특정 파이프라인 단계의 상태를 업데이트합니다.

    사용 예시:
    update_vod_pipeline_step(db, vod_obj, "stage1_http", "completed", {"size_mb": 2048})
    update_vod_pipeline_step(db, vod_obj, "stage2_processing", "failed", {"error": "ASR timeout"})
    """
    try:
        # 현재 status_details를 가져오거나, 없으면 새로 생성
        current_details = vod.status_details if vod.status_details else {}

        # 업데이트할 단계 정보 생성
        step_update = {"status": status}
        if metadata:
            step_update.update(metadata)

        # 새로운 정보로 덮어쓰기
        current_details[step_name] = step_update

        # SQLAlchemy가 JSONB 필드의 내부 변경을 감지하도록 명시적으로 플래그 설정
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(vod, "status_details")

        db.commit()
        logger.info(f"Updated pipeline step '{step_name}' to '{status}' for video_no: {vod.video_no}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update pipeline step for video_no {vod.video_no}: {e}")
        return False


def update_vod_process_status(db: Session, vod: ChzzkVodORM, status: VodProcessStatus) -> bool:
    """VOD의 전체적인 process_status를 업데이트합니다."""
    try:
        vod.process_status = status
        # 완료 또는 최종 실패 시각 기록
        if status in [VodProcessStatus.COMPLETED, VodProcessStatus.FAILED]:
            vod.processed_at = func.now()

        db.commit()
        logger.info(f"Updated overall status to '{status.value}' for video_no: {vod.video_no}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update overall status for video_no {vod.video_no}: {e}")
        return False


# --- 4. 분석 결과 (chzzk_analysis_results) 관리 함수 ---


def create_analysis_result(db: Session, vod: ChzzkVodORM, result_data: dict) -> ChzzkAnalysisResultORM | None:
    """분석 완료 후 최종 결과물 정보를 DB에 생성합니다."""
    try:
        db_result = ChzzkAnalysisResultORM(vod_id=vod.id, **result_data)
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        logger.success(f"✅ Created analysis result for video_no: {vod.video_no}")
        return db_result
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create analysis result for video_no {vod.video_no}: {e}")
        return None
