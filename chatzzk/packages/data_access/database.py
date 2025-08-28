import os
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 1. ORM 모델 임포트
from chatzzk.packages.schemas.db_models import (
    Base,
    ChzzkVodORM,
    ChzzkVodProcessingStatusORM,
)

# --- 1. DB 연결 및 세션 설정 ---

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set.")

# 'pool_recycle' 옵션: 오랜 시간 후 DB 연결이 끊기는 것을 방지
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


# --- 2. VOD 정보 (chzzk_vods) CRUD 함수 ---


def create_vod_and_status(db: Session, vod_data: dict) -> ChzzkVodORM | None:
    """
    Pydantic 모델을 받아, 새로운 VOD 정보와 초기 처리 상태를 DB에 함께 생성합니다.
    ORM 모델에 존재하는 필드만 안전하게 추출하여 사용합니다.
    """
    video_no = vod_data.get("video_no")
    try:
        db_vod = ChzzkVodORM(**vod_data)

        # 3. VOD 처리 상태도 함께 생성
        db_status = ChzzkVodProcessingStatusORM()
        db_vod.status = db_status  # 관계 설정

        db.add(db_vod)
        db.commit()
        db.refresh(db_vod)
        logger.success(f"✅ Created VOD and initial status for video_no: {video_no}")
        return db_vod

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create VOD and status for video_no {video_no}: {e}")
        return None


def get_vod_by_video_no(db: Session, video_no: str) -> ChzzkVodORM | None:
    """video_no를 사용하여 VOD 정보를 조회합니다."""
    return db.query(ChzzkVodORM).filter(ChzzkVodORM.video_no == video_no).first()


# --- 3. VOD 처리 상태 (chzzk_vod_processing_status) CRUD 함수 ---


def get_status_by_video_no(db: Session, video_no: str) -> ChzzkVodProcessingStatusORM | None:
    """video_no를 사용하여 VOD 처리 상태를 조회합니다 (JOIN 활용)."""
    return db.query(ChzzkVodProcessingStatusORM).join(ChzzkVodORM).filter(ChzzkVodORM.video_no == video_no).first()


# def get_pending_vods_for_processing(db: Session, limit: int = 10) -> list[ChzzkVodORM]:
#     """
#     'PENDING' 상태인 VOD들을 가져와 'PROCESSING'으로 상태를 변경한 후 반환합니다.
#     """
#     pending_statuses = (
#         db.query(ChzzkVodProcessingStatusORM)
#         .filter(ChzzkVodProcessingStatusORM.workflow_status == "PENDING")
#         .limit(limit)
#         .with_for_update(skip_locked=True)
#         .all()
#     )

#     if not pending_statuses:
#         return []

#     vods_to_process = []
#     for status in pending_statuses:
#         status.workflow_status = "PROCESSING"
#         vods_to_process.append(status.vod)  # relationship을 통해 VOD 정보에 접근

#     db.commit()
#     logger.info(f"Picked up {len(vods_to_process)} VODs for processing.")
#     return vods_to_process


# def update_vod_status_flags(db: Session, video_no: str, **kwargs) -> bool:
#     """
#     특정 VOD의 처리 상태 플래그(is_chat_saved 등)를 업데이트합니다.

#     사용 예시:
#     update_vod_status_flags(db, "12345", is_chat_saved=True, context_file_path="/path/to/file.jsonl")
#     """
#     status = get_status_by_video_no(db, video_no)
#     if not status:
#         logger.error(f"Status not found for video_no {video_no} during update.")
#         return False

#     try:
#         for key, value in kwargs.items():
#             if hasattr(status, key):
#                 setattr(status, key, value)
#             else:
#                 logger.warning(f"Attribute '{key}' not found in ChzzkVodProcessingStatusORM.")

#         db.commit()
#         logger.info(f"Updated status for video_no {video_no} with: {kwargs}")
#         return True
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Failed to update status for video_no {video_no}: {e}")
#         return False
