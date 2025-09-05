# 개발환경에서 나하의 vod에 대해 테스트 용도로만 사용될 것
import os

from loguru import logger

# --- 의존성 임포트 ---
from chatzzk.packages.constants.service_codes import WorkflowStatus
from chatzzk.packages.data_access import database
from chatzzk.services.collector.jobs.preprocess_vod import (
    run_preprocessing_pipeline,
)
from chatzzk.services.collector.jobs.process_context import run_processing_pipeline
from chatzzk.services.collector.jobs.workspace import VodWorkspace


# @celery_app.task(name="jobs.process_single_vod")
def process_single_vod(video_no: str, cleanup: bool = False):
    """
    DB에 'PENDING' 상태로 저장된 단일 VOD의 실제 데이터를 처리합니다.
    (MP4, 채팅 다운로드 -> WAV 추출 -> ASR -> Context 저장)
    """
    logger.info(f"🚀 Starting data processing for VOD: {video_no}")
    workspace = VodWorkspace(video_no)

    try:
        # --- Step 1: 작업 시작 및 상태 잠금 ---
        with database.get_db_session() as db:
            status = database.get_status_by_video_no(db, video_no)
            if not status or status.workflow_status == WorkflowStatus.COMPLETED:
                logger.warning("VOD not processable. Skipping.")
                return

            if status.workflow_status == WorkflowStatus.PENDING_PREPROCESSING:
                workspace.setup()

            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.PREPROCESSING_IN_PROGRESS)

        # --- 2. 파이프라인 1단계: 전처리 실행 ---
        run_preprocessing_pipeline(video_no, workspace)
        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.PENDING_PROCESSING)

        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.PROCESSING_IN_PROGRESS)

        # --- 3. 파이프라인 2단계: 핵심 처리 실행 ---
        run_processing_pipeline(video_no, workspace)
        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.PENDING_POSTPROCESSING)

        # --- 4. 파이프라인 3단계: 후처리 실행 (향후 구현) ---
        # run_postprocessing_pipeline(video_no)

        logger.success(f"🎉 [{video_no}] All processing steps completed successfully.")
        if cleanup:
            workspace.cleanup()

    except Exception as e:
        logger.opt(exception=True).error(f"❌ Pipeline failed for VOD {video_no}: {e}")

        # --- 실패 처리 (별도의 트랜잭션) ---
        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.FAILED)

        raise  # Celery 등이 실패를 인지하도록 에러를 다시 발생시킴


if __name__ == "__main__":
    VIDEO_NO = os.environ.get("VIDEO_NO")
    VIDEO_NO_STR = str(VIDEO_NO)
    CHANNEL_ID = os.environ.get("CHANNEL_ID")

    process_single_vod(VIDEO_NO_STR)
