from loguru import logger

from chatzzk.packages.constants.service_codes import WorkflowStatus
from chatzzk.packages.data_access import database
from chatzzk.packages.media_processing.audio import extract_wav_from_video
from chatzzk.services.collector.jobs.workspace import VodWorkspace


def run_processing_pipeline(video_no: str, workspace: VodWorkspace):
    """처리 파이프라인 (WAV 추출, ASR, Context 생성)을 실행합니다."""
    logger.info(f"[{video_no}] Starting processing pipeline...")

    # 1. WAV 추출
    _extract_wav(video_no, workspace)

    # 2. ASR 및 Context 생성/저장 (향후 구현)
    # _run_asr_and_merge(video_no, workspace)

    logger.info(f"[{video_no}] Processing pipeline finished.")


def _extract_wav(video_no: str, workspace: VodWorkspace):
    try:
        with database.get_db_session() as db:
            if database.get_status_by_video_no(db, video_no).is_wav_extracted:
                logger.info(f"[{video_no}] WAV already extracted. Skipping.")
                return

        extract_wav_from_video(workspace.paths.mp4, workspace.paths.wav)

        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, is_wav_extracted=True)

        logger.info(f"[{video_no}] WAV extracted.")

    except Exception as e:
        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.FAILED)
        logger.opt(exception=True).error(f"❌ Pipeline failed for VOD {video_no}: {e}")
