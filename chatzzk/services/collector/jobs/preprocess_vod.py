# preprocess_vod.py
# (이 파일은 두 개의 worker job과 하나의 orchestrator job을 포함)

from loguru import logger

from chatzzk.packages.data_access import database
from chatzzk.packages.utils.downloader import download_file_from_url
from chatzzk.services.collector.jobs.workspace import VodWorkspace
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient
from chatzzk.services.collector.settings import collector_settings

chzzk_client = ChzzkPlatformClient()


def run_preprocessing_pipeline(video_no: str, workspace: VodWorkspace):
    """전처리 파이프라인 (채팅 크롤링 및 비디오 다운로드)을 순차적으로 실행합니다."""
    logger.info(f"[{video_no}] Starting preprocessing pipeline...")

    # 1. 채팅 크롤링
    _crawl_chat(video_no, workspace)

    # 2. 비디오 다운로드
    _download_video(video_no, workspace)

    logger.info(f"[{video_no}] Preprocessing pipeline finished.")


def _crawl_chat(video_no: str, workspace: VodWorkspace):
    with database.get_db_session() as db:
        if database.get_status_by_video_no(db, video_no).is_chat_crawled:
            logger.info(f"[{video_no}] Chat already crawled. Skipping.")
            return

    chat_contexts = chzzk_client.crawl_chat(video_no)
    with open(workspace.paths.chat_context, "w", encoding="utf-8") as f:
        for entry in chat_contexts:
            f.write(entry.model_dump_json() + "\n")

    with database.get_db_session() as db:
        database.update_status_and_commit(db, video_no, is_chat_crawled=True)

    logger.info(f"[{video_no}] Chat crawled.")


def _download_video(video_no: str, workspace: VodWorkspace):
    with database.get_db_session() as db:
        if database.get_status_by_video_no(db, video_no).is_mp4_downloaded:
            logger.info(f"[{video_no}] video already downloaded. Skipping.")
            return

    logger.info(f"[{video_no}] Step 4: Downloading MP4...")
    details = chzzk_client.fetch_vod_details(video_no)
    if not details:
        raise ValueError("Failed to fetch VOD details (videoId, inKey).")
    _, video_id, in_key = details

    stream_reps = chzzk_client.fetch_all_stream_representations(video_id, in_key)
    if not stream_reps:
        raise ValueError("No stream URLs found.")

    resolution_index = collector_settings.target_index_for_video_resolution
    if resolution_index >= len(stream_reps):
        resolution_index = -1
    download_url = stream_reps[resolution_index][1]

    # 임시 파일로 다운로드
    mp4_file_path = workspace.paths.mp4
    download_file_from_url(url=download_url, destination_path=mp4_file_path, session=chzzk_client.session)

    with database.get_db_session() as db:
        database.update_status_and_commit(db, video_no, is_mp4_downloaded=True)

    logger.info(f"[{video_no}] Video downloaded.")
