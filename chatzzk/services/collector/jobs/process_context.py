import numpy as np
from loguru import logger

from chatzzk.packages.constants.service_codes import ASR_DUMMY_PAY_AMOUNT, ContextType
from chatzzk.packages.data_access import database
from chatzzk.packages.data_access.storage.factory import create_storage_manager
from chatzzk.packages.media_processing.audio import extract_wav_from_video, load_audio
from chatzzk.packages.media_processing.context import merge_context_files
from chatzzk.packages.ml_clients.asr.factory import create_asr_client
from chatzzk.packages.ml_clients.vad.factory import create_vad_client
from chatzzk.packages.schemas.data_models import StreamContextEntry
from chatzzk.services.collector.jobs.workspace import VodWorkspace
from chatzzk.services.collector.settings import collector_settings

try:
    vad_config = collector_settings.vad_model_config
    vad_client = create_vad_client(model_config=vad_config)

    asr_config = collector_settings.asr_model_config
    asr_client = create_asr_client(model_config=asr_config, models_base_dir="models")

    storage_config = collector_settings.storage_config
    storage_manager = create_storage_manager(storage_config=storage_config)

except (AttributeError, ValueError) as e:
    logger.critical(f"Failed to initialize ML clients or storage manager from settings: {e}")
    # 설정이 잘못되면 이 모듈은 동작할 수 없으므로, 즉시 에러 발생
    raise e


def run_processing_pipeline(video_no: str, workspace: VodWorkspace):
    """처리 파이프라인 (WAV 추출, ASR, Context 생성)을 실행합니다."""
    logger.info(f"[{video_no}] Starting processing pipeline...")

    # 1. WAV 추출
    _extract_wav(video_no, workspace)

    # 2. ASR 및 Context 생성/저장
    _create_and_save_asr_context(video_no, workspace)

    # 3. 저장된 asr_context, chat_context로 merged_context 생성/저장
    _create_and_save_merged_context(video_no, workspace)

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
        logger.opt(exception=True).error(f"❌ extract_wav failed for VOD {video_no}: {e}")
        raise e


def _perform_vad(audio_np: np.ndarray) -> list[tuple[int, int]]:
    logger.info("Detecting speech segments with VAD...")
    timestamps = vad_client.detect_speech(audio_np)
    logger.info(f"VAD detected {len(timestamps)} speech segments.")
    return timestamps


def _perform_asr_on_segments(
    audio_np: np.ndarray, timestamps: list[tuple[int, int]]
) -> list[tuple[tuple[int, int], str]]:
    results = []
    logger.info(f"Performing ASR on {len(timestamps)} audio segments...")
    for start_sample, end_sample in timestamps:
        segment_audio = audio_np[start_sample:end_sample]
        transcription_text = asr_client.transcribe(segment_audio)
        if transcription_text:
            results.append(((start_sample, end_sample), transcription_text))
    return results


def _create_asr_context(asr_results: list[tuple[tuple[int, int], str]], sample_rate: int) -> list[StreamContextEntry]:
    asr_contexts = []
    for (start_sample, end_sample), text in asr_results:
        average_sample = (start_sample + end_sample) / 2
        timestamp_ms = int((average_sample / sample_rate) * 1000)

        asr_contexts.append(
            StreamContextEntry(
                timestamp_ms=timestamp_ms, type=ContextType.ASR, content=text, pay_amount=ASR_DUMMY_PAY_AMOUNT
            )
        )
    return asr_contexts


def _create_and_save_asr_context(video_no: str, workspace: VodWorkspace):
    try:
        with database.get_db_session() as db:
            if database.get_status_by_video_no(db, video_no).is_asr_completed:
                logger.info(f"[{video_no}] ASR already completed. Skipping.")
                return

        audio_np, sr = load_audio(workspace.paths.wav)

        timestamps = _perform_vad(audio_np)
        asr_results = _perform_asr_on_segments(audio_np, timestamps)
        asr_context = _create_asr_context(asr_results, sr)

        with open(workspace.paths.asr_context, "w", encoding="utf-8") as f:
            for entry in asr_context:
                f.write(entry.model_dump_json() + "\n")

        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, is_asr_completed=True)
    except Exception as e:
        logger.opt(exception=True).error(f"❌ run_vad_and_asr failed for VOD {video_no}: {e}")
        raise e


def _create_and_save_merged_context(video_no: str, workspace: VodWorkspace):
    """
    chat_context와 asr_context를 병합하여 merged_context 파일로 저장합니다.
    """
    try:
        with database.get_db_session() as db:
            if database.get_status_by_video_no(db, video_no).is_context_saved:
                logger.info(f"[{video_no}] vod_context already saved. Skipping.")
                return

        chat_context_path = workspace.paths.chat_context
        asr_context_path = workspace.paths.asr_context

        merged_context = merge_context_files(chat_context_path, asr_context_path)
        merged_context_object_name = storage_manager.save_context(video_no, merged_context)

        logger.info(f"[{video_no}] Merged context saved to {merged_context_object_name}")
        with database.get_db_session() as db:
            database.update_status_and_commit(db, video_no, is_context_saved=True)

    except Exception as e:
        logger.opt(exception=True).error(f"❌ Failed to create merged context for VOD {video_no}: {e}")
        raise e
