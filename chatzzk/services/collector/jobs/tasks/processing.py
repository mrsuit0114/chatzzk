import shutil
from pathlib import Path

import numpy as np
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
from chatzzk.packages.data_access.repositories.analysis import AnalysisResultRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.data_access.storage.factory import create_storage_manager
from chatzzk.packages.media_processing.audio import extract_wav_from_video, load_audio
from chatzzk.packages.media_processing.context import merge_context_files
from chatzzk.packages.ml_clients.asr.factory import create_asr_client
from chatzzk.packages.ml_clients.vad.factory import create_vad_client
from chatzzk.packages.schemas.data_models import StreamContextEntry
from chatzzk.packages.schemas.db_models import ChzzkVodORM
from chatzzk.packages.utils.downloader import download_file_from_url
from chatzzk.services.collector.celery_app import celery_collector_app
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient
from chatzzk.services.collector.settings import collector_settings

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
@celery_collector_app.task(name="collector.process_vod_to_context", bind=True, max_retries=2, default_retry_delay=600)
def process_vod_to_context(self, vod_pk: int):
    """[Celery Task] VOD 하나를 받아 video_context.jsonl을 생성하고 스토리지에 업로드합니다."""

    video_no = f"vod_pk:{vod_pk}"  # 에러 로깅을 위해 vod_pk로 초기화
    try:
        # Step 0: Initial DB Read and Status Update
        with database.get_db_session() as db:
            vod_repo = VodRepository(db)
            vod = db.get(ChzzkVodORM, vod_pk)
            if not vod:
                logger.error(f"VOD with id {vod_pk} not found. Aborting.")
                return f"VOD {vod_pk} not found."

            video_no = vod.video_no  # 실제 video_no로 업데이트
            status_details = vod.status_details or {}
            logger.info(
                f"🚀 [Task ID: {self.request.id}] Starting VOD processing for vod_pk: {vod_pk} (video_no: {video_no})"
            )
            vod_repo.update_process_status(vod, VodProcessStatus.PROCESSING)

        paths = prepare_workspace(video_no)

        # --- 1단계: 데이터 수집 (HTTP 요청) ---
        if status_details.get(PipelineStep.CRAWL_CHAT, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            chat_contexts = chzzk_client.crawl_chat(video_no)
            with open(paths.chat_context, "w", encoding="utf-8") as f:
                for entry in chat_contexts:
                    f.write(entry.model_dump_json() + "\n")
            with database.get_db_session() as db:
                vod_repo = VodRepository(db)
                vod = db.get(ChzzkVodORM, vod_pk)
                vod_repo.update_pipeline_step(vod, PipelineStep.CRAWL_CHAT, StepStatus.COMPLETED)

        if status_details.get(PipelineStep.DOWNLOAD_VIDEO, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            details = chzzk_client.fetch_vod_details(video_no)
            _, video_id, in_key = details
            stream_reps = chzzk_client.fetch_all_stream_representations(video_id, in_key)
            download_url = stream_reps[TARGET_INDEX_FOR_VIDEO_RESOLUTION][1]  # 최저 화질
            download_file_from_url(url=download_url, destination_path=paths.mp4, session=chzzk_client.session)
            with database.get_db_session() as db:
                vod_repo = VodRepository(db)
                vod = db.get(ChzzkVodORM, vod_pk)
                vod_repo.update_pipeline_step(vod, PipelineStep.DOWNLOAD_VIDEO, StepStatus.COMPLETED)

        # --- 2단계: 미디어 처리 (로컬/CPU 작업) ---
        if status_details.get(PipelineStep.EXTRACT_WAV, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            extract_wav_from_video(paths.mp4, paths.wav)
            with database.get_db_session() as db:
                vod_repo = VodRepository(db)
                vod = db.get(ChzzkVodORM, vod_pk)
                vod_repo.update_pipeline_step(vod, PipelineStep.EXTRACT_WAV, StepStatus.COMPLETED)

        if status_details.get(PipelineStep.PERFORM_ASR, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            audio_np, sr = load_audio(paths.wav)
            timestamps = vad_client.detect_speech(audio_np)
            asr_context = _perform_asr_and_create_context(audio_np, timestamps, sr)
            with open(paths.asr_context, "w", encoding="utf-8") as f:
                for entry in asr_context:
                    f.write(entry.model_dump_json() + "\n")
            with database.get_db_session() as db:
                vod_repo = VodRepository(db)
                vod = db.get(ChzzkVodORM, vod_pk)
                vod_repo.update_pipeline_step(vod, PipelineStep.PERFORM_ASR, StepStatus.COMPLETED)

        # --- 3단계: 컨텍스트 병합 및 업로드 ---
        if status_details.get(PipelineStep.MERGE_AND_UPLOAD, {}).get(PipelineStep.STATUS_KEY) != StepStatus.COMPLETED:
            merged_context = merge_context_files(paths.chat_context, paths.asr_context)
            context_file_key = storage_manager.save_context(video_no, merged_context)

            if context_file_key:
                with database.get_db_session() as db:
                    vod_repo = VodRepository(db)
                    analysis_repo = AnalysisResultRepository(db)
                    vod = db.get(ChzzkVodORM, vod_pk)

                    result_data = {AnalysisResultKey.CONTEXT_FILE_KEY: context_file_key}
                    analysis_repo.create(vod, result_data)
                    vod_repo.update_pipeline_step(vod, PipelineStep.MERGE_AND_UPLOAD, StepStatus.COMPLETED)

        cleanup_workspace(video_no)
        return f"Successfully processed VOD {vod_pk}"

    except Exception as e:
        logger.opt(exception=True).error(f"❌ Error in VOD processing for {video_no}: {e}")
        # 실패 시에는 별도 세션을 열어 안전하게 상태를 FAILED로 업데이트
        with database.get_db_session() as db:
            vod_repo = VodRepository(db)
            vod_to_fail = db.get(ChzzkVodORM, vod_pk)
            if vod_to_fail:
                vod_repo.update_process_status(vod_to_fail, VodProcessStatus.FAILED)
        raise self.retry(exc=e) from e
