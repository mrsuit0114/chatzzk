# 개발환경에서 나하의 vod에 대해 테스트 용도로만 사용될 것


from datetime import UTC, datetime

from loguru import logger

# --- 의존성 임포트 ---
from chatzzk.packages.constants.service_codes import WorkflowStatus
from chatzzk.packages.data_access import database
from chatzzk.packages.media_processing.audio import extract_wav_from_video
from chatzzk.packages.utils.downloader import download_file_from_url
from chatzzk.services.collector.jobs.workspace import VodWorkspace
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)
from chatzzk.services.collector.settings import collector_settings

chzzk_client = ChzzkPlatformClient()


# @celery_app.task(name="jobs.process_single_vod")
def process_single_vod(video_no: str):
    """
    DB에 'PENDING' 상태로 저장된 단일 VOD의 실제 데이터를 처리합니다.
    (MP4, 채팅 다운로드 -> WAV 추출 -> ASR -> Context 저장)
    """
    logger.info(f"🚀 Starting data processing for VOD: {video_no}")
    workspace = VodWorkspace(video_no)

    try:
        # --- Step 1: 작업 시작 및 상태 잠금 ---
        with database.get_db_session() as db:
            status_orm = database.get_status_by_video_no(db, video_no)
            if not status_orm or status_orm.workflow_status == WorkflowStatus.COMPLETED:
                logger.warning(f"VOD {video_no} is not processable. Skipping.")
                return

            if status_orm.workflow_status == WorkflowStatus.PENDING:
                workspace.setup()

            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.PROCESSING)
            logger.info(f"[{video_no}] Status updated to PROCESSING.")

        # --- Step 2: 채팅 데이터 크롤링 및 저장 (두 번째 트랜잭션) ---
        with database.get_db_session() as db:
            is_chat_crawled = database.get_status_by_video_no(db, video_no).is_chat_crawled

        if not is_chat_crawled:
            logger.info(f"[{video_no}] Step 3: Crawling chat data...")
            # 3-1. 크롤링
            chat_contexts = chzzk_client.crawl_chat(video_no)

            # 3-2. 임시 파일로 저장
            chat_file_path = workspace.paths.chat
            with open(chat_file_path, "w", encoding="utf-8") as f:
                for entry in chat_contexts:
                    f.write(entry.model_dump_json() + "\n")
            logger.info(f"[{video_no}] Chat data saved to temporary file: {chat_file_path}")

            with database.get_db_session() as db:
                database.update_status_and_commit(db, video_no, is_chat_crawled=True)
        else:
            logger.info(f"[{video_no}] Step 3: Chat data already crawled. Skipping.")

        # --- Step 3: VOD 상세 정보 (재생 키) 가져오기 ---
        details = chzzk_client.fetch_vod_details(video_no)
        if not details:
            raise ValueError("Failed to fetch VOD details (videoId, inKey).")
        _, video_id, in_key = details

        # --- Step 4: MP4 다운로드 (세 번째 트랜잭션) ---
        with database.get_db_session() as db:
            is_mp4_downloaded = database.get_status_by_video_no(db, video_no).is_mp4_downloaded

        if not is_mp4_downloaded:
            logger.info(f"[{video_no}] Step 4: Downloading MP4...")
            # 4-1. 스트림 URL 획득
            stream_reps = chzzk_client.fetch_all_stream_representations(video_id, in_key)
            if not stream_reps:
                raise ValueError("No stream URLs found.")

            resolution_index = collector_settings.TARGET_INDEX_FOR_VIDEO_RESOLUTION
            if resolution_index >= len(stream_reps):
                resolution_index = -1
            download_url = stream_reps[resolution_index][1]

            # 4-2. 임시 파일로 다운로드
            mp4_file_path = workspace.paths.mp4
            download_file_from_url(url=download_url, destination_path=mp4_file_path, session=chzzk_client.session)

            # 4-3. DB 상태 갱신 및 커밋
            with database.get_db_session() as db:
                database.update_status_and_commit(db, video_no, is_mp4_downloaded=True)
        else:
            logger.info(f"[{video_no}] MP4 already downloaded. Skipping.")

        # --- Step 5: WAV 오디오 추출 (네 번째 트랜잭션) ---
        with database.get_db_session() as db:
            is_wav_extracted = database.get_status_by_video_no(db, video_no).is_wav_extracted

        if not is_wav_extracted:
            logger.info(f"[{video_no}] Step 5: Extracting WAV from MP4...")
            # 5-1. WAV 추출
            extract_wav_from_video(video_path=workspace.paths.mp4, output_wav_path=workspace.paths.wav)

            with database.get_db_session() as db:
                database.update_status_and_commit(db, video_no, is_wav_extracted=True)
        else:
            logger.info(f"[{video_no}] Step 5: WAV already extracted. Skipping.")

        # ... ASR 및 Context 생성 로직 ...
        # ... 최종 Context 파일을 영구 스토리지(MinIO)에 업로드 ...

        # --- 최종 성공 처리 ---
        # --- 최종 성공 처리 (마지막 트랜잭션) ---
        with database.get_db_session() as db:
            database.update_status_and_commit(
                db, video_no, workflow_status=WorkflowStatus.COMPLETED, completed_at=datetime.now(UTC)
            )
        logger.success(f"🎉 [{video_no}] All processing steps completed successfully.")
        workspace.cleanup()

    except Exception as e:
        logger.opt(exception=True).error(f"❌ Pipeline failed for VOD {video_no}: {e}")

        # --- 실패 처리 (별도의 트랜잭션) ---
        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, workflow_status=WorkflowStatus.FAILED)

        raise  # Celery 등이 실패를 인지하도록 에러를 다시 발생시킴


if __name__ == "__main__":
    VIDEO_NO = 8982863
    VIDEO_NO_STR = str(VIDEO_NO)
    CHANNEL_ID = "c847a58a1599988f6154446c75366523"

    process_single_vod(VIDEO_NO_STR)
