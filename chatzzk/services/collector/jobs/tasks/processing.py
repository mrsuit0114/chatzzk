import shutil
from collections import namedtuple
from pathlib import Path

import numpy as np  # process_context.py에서 사용
from loguru import logger

from chatzzk.packages.constants.service_codes import (
    ASR_DUMMY_PAY_AMOUNT,
    AnalysisResultKey,
    ContextType,
    PipelineStep,
    StepStatus,
    TempFile,
    VodProcessStatus,
)
from chatzzk.packages.data_access import database
from chatzzk.packages.data_access.storage.factory import create_storage_manager
from chatzzk.packages.media_processing.audio import extract_wav_from_video, load_audio
from chatzzk.packages.media_processing.context import merge_context_files
from chatzzk.packages.ml_clients.asr.factory import create_asr_client
from chatzzk.packages.ml_clients.vad.factory import create_vad_client

# --- Celery 앱 및 DB 접근 모듈 ---
from chatzzk.packages.schemas.data_models import StreamContextEntry

# --- 필요한 ORM 모델 ---
from chatzzk.packages.schemas.db_models import ChzzkVodORM

# --- 기존 코드에서 가져온 의존성 ---
from chatzzk.packages.utils.downloader import download_file_from_url
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient
from chatzzk.services.collector.settings import collector_settings

# Define a simple mock object for the self argument
MockRequest = namedtuple("MockRequest", ["id"])
MockSelf = namedtuple("MockSelf", ["request", "retry"])


# `self.retry`를 모킹하기 위한 함수. 예외를 다시 발생시켜 디버깅을 돕는다.
def mock_retry(exc):
    print(f"[MOCK] Called self.retry for exception: {type(exc).__name__}")
    raise exc


# Mock `self` 객체 생성
mock_self_obj = MockSelf(request=MockRequest(id="local_test-task-12345"), retry=mock_retry)
# --- 모듈 레벨 초기화 ---
# 이 Task를 실행하는 워커는 이 클라이언트들을 메모리에 로드하게 됨.
try:
    chzzk_client = ChzzkPlatformClient()
    vad_client = create_vad_client(model_config=collector_settings.vad_model_config)
    asr_client = create_asr_client(model_config=collector_settings.asr_model_config, models_base_dir="models")
    storage_manager = create_storage_manager(storage_config=collector_settings.storage_config)
except Exception as e:
    logger.critical(f"Failed to initialize clients in processing.py: {e}")
    raise  # 워커 시작 시 실패하도록 함

TARGET_INDEX_FOR_VIDEO_RESOLUTION = collector_settings.target_index_for_video_resolution


# --- 임시 작업 공간 관리 ---
def prepare_workspace(video_no: str):
    """VOD 처리를 위한 임시 디렉토리를 준비하고 경로 객체를 반환합니다."""
    base_dir = Path(collector_settings.workspace_base_dir)
    workspace_dir = base_dir / video_no
    workspace_dir.mkdir(parents=True, exist_ok=True)

    class Paths:
        mp4 = workspace_dir / TempFile.VIDEO
        wav = workspace_dir / TempFile.AUDIO
        chat_context = workspace_dir / TempFile.CHAT_CONTEXT
        asr_context = workspace_dir / TempFile.ASR_CONTEXT

    logger.info(f"[{video_no}] Prepared temporary workspace at: {workspace_dir}")
    return Paths()


def cleanup_workspace(video_no: str):
    """VOD 처리 임시 디렉토리를 정리합니다."""
    base_dir = Path(collector_settings.workspace_base_dir)
    workspace_dir = base_dir / video_no
    if workspace_dir.exists():
        try:
            shutil.rmtree(workspace_dir)
            logger.info(f"[{video_no}] Cleaned up temporary workspace: {workspace_dir}")
        except OSError as e:
            logger.error(f"Failed to clean up workspace {workspace_dir}: {e}")


def _update_pipeline_step_with_session(vod_id: int, step_name: str, status: str, metadata: dict | None = None):
    """
    VOD 파이프라인의 특정 단계를 업데이트합니다.
    이 함수는 자체적으로 DB 세션을 생성하고 닫으므로, 장기 실행 작업에 적합합니다.
    """
    try:
        with database.get_db_session() as db:
            vod = db.get(ChzzkVodORM, vod_id)
            if not vod:
                logger.warning(f"VOD with id {vod_id} not found for status update. Skipping.")
                return

            # database.py의 함수를 호출
            database.update_vod_pipeline_step(db, vod, step_name, status, metadata)
    except Exception as e:
        logger.error(f"Failed to update pipeline step '{step_name}' for vod_id {vod_id}: {e}")
        raise


def _perform_asr_and_create_context(
    audio_np: np.ndarray, timestamps: list[tuple[int, int]], sample_rate: int = 16000
) -> list[StreamContextEntry]:
    """
    오디오 세그먼트를 ASR 처리하고 StreamContextEntry 리스트를 생성합니다.
    """
    asr_context_entries = []
    logger.info(f"Performing ASR on {len(timestamps)} audio segments...")

    for start_sample, end_sample in timestamps:
        segment_audio = audio_np[start_sample:end_sample]
        transcription_text = asr_client.transcribe(segment_audio)

        if transcription_text:
            # ASR 결과를 바로 StreamContextEntry로 변환
            average_sample = (start_sample + end_sample) / 2
            timestamp_ms = int((average_sample / sample_rate) * 1000)

            asr_context_entries.append(
                StreamContextEntry(
                    timestamp_ms=timestamp_ms,
                    type=ContextType.ASR,
                    content=transcription_text,
                    pay_amount=ASR_DUMMY_PAY_AMOUNT,
                )
            )

    return asr_context_entries


# --- 메인 Celery Task ---
# @celery_collector_app.task(name="collector.process_vod_to_context", bind=True, max_retries=2, default_retry_delay=600)
def process_vod_to_context(self, vod_id: int):
    """[Celery Task] VOD 하나를 받아 video_context.jsonl을 생성하고 스토리지에 업로드합니다."""

    # 헬퍼 함수들을 호출하고 상태를 관리하는 오케스트레이션 로직
    try:
        with database.get_db_session() as db:
            vod_to_process = db.get(ChzzkVodORM, vod_id)
            if not vod_to_process:
                logger.error(f"VOD with id {vod_id} not found. Aborting.")
                return f"VOD {vod_id} not found."
            database.update_vod_process_status(db, vod_to_process, VodProcessStatus.PROCESSING)
            video_no = vod_to_process.video_no
            status_details = vod_to_process.status_details or {}

        logger.info(
            f"🚀 [Task ID: {self.request.id}] Starting VOD processing for vod_id: {vod_id} (video_no: {video_no})"
        )
        paths = prepare_workspace(video_no)

        # --- 1단계: 데이터 수집 (HTTP 요청) ---
        if status_details.get(PipelineStep.CRAWL_CHAT, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            chat_contexts = chzzk_client.crawl_chat(video_no)
            with open(paths.chat_context, "w", encoding="utf-8") as f:
                for entry in chat_contexts:
                    f.write(entry.model_dump_json() + "\n")
            _update_pipeline_step_with_session(vod_id, PipelineStep.CRAWL_CHAT, StepStatus.COMPLETED)

        if status_details.get(PipelineStep.DOWNLOAD_VIDEO, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            details = chzzk_client.fetch_vod_details(video_no)
            _, video_id, in_key = details
            stream_reps = chzzk_client.fetch_all_stream_representations(video_id, in_key)
            download_url = stream_reps[TARGET_INDEX_FOR_VIDEO_RESOLUTION][1]  # 최저 화질
            download_file_from_url(url=download_url, destination_path=paths.mp4, session=chzzk_client.session)
            _update_pipeline_step_with_session(vod_id, PipelineStep.DOWNLOAD_VIDEO, StepStatus.COMPLETED)

        # --- 2단계: 미디어 처리 (로컬/CPU 작업) ---
        if status_details.get(PipelineStep.EXTRACT_WAV, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            extract_wav_from_video(paths.mp4, paths.wav)
            _update_pipeline_step_with_session(vod_id, PipelineStep.EXTRACT_WAV, StepStatus.COMPLETED)

        if status_details.get(PipelineStep.PERFORM_ASR, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            audio_np, sr = load_audio(paths.wav)
            timestamps = vad_client.detect_speech(audio_np)
            asr_context = _perform_asr_and_create_context(audio_np, timestamps, sr)
            with open(paths.asr_context, "w", encoding="utf-8") as f:
                for entry in asr_context:
                    f.write(entry.model_dump_json() + "\n")
            _update_pipeline_step_with_session(
                vod_id, PipelineStep.PERFORM_ASR, StepStatus.COMPLETED
            )  # , {"model": asr_client.model_name})

        # --- 3단계: 컨텍스트 병합 및 업로드 ---
        if status_details.get(PipelineStep.MERGE_AND_UPLOAD, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            merged_context = merge_context_files(paths.chat_context, paths.asr_context)
            context_file_key = storage_manager.save_context(video_no, merged_context)

            if context_file_key:
                with database.get_db_session() as db:
                    vod_to_complete = db.get(ChzzkVodORM, vod_id)
                    # 최종 결과 저장
                    result_data = {AnalysisResultKey.CONTEXT_FILE_KEY: context_file_key}
                    database.create_analysis_result(
                        db, vod_to_complete, result_data
                    )  # 중복된 vod.id로 저장하면 에러가 나는데 위에서는 완료됐다해서 들어오질않으니 cleanup도 안되네
                    database.update_vod_pipeline_step(
                        db, vod_to_complete, PipelineStep.MERGE_AND_UPLOAD, StepStatus.COMPLETED
                    )
                cleanup_workspace(video_no)

        return f"Successfully processed VOD {vod_id}"

    except Exception as e:
        logger.opt(exception=True).error(f"❌ Error in VOD processing for {vod_id}: {e}")
        with database.get_db_session() as db:
            vod_to_fail = db.get(ChzzkVodORM, vod_id)
            database.update_vod_process_status(db, vod_to_fail, VodProcessStatus.FAILED)
        raise self.retry(exc=e) from e


if __name__ == "__main__":
    test_vod_id = 5
    process_vod_to_context(mock_self_obj, test_vod_id)
