import shutil
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from chatzzk.packages.constants.service_codes import (
    ASR_DUMMY_PAY_AMOUNT,
    AnalysisResultKey,
    ContextType,
    PipelineStep,
    StepStatus,
    TempFile,
    VodProcessStatus,
)
from chatzzk.packages.data_access.repositories.analysis import AnalysisResultRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.data_access.storage.base import StorageInterface
from chatzzk.packages.media_processing.audio import extract_wav_from_video, load_audio
from chatzzk.packages.media_processing.context import merge_context_files
from chatzzk.packages.ml_clients.asr.base import ASRClientInterface
from chatzzk.packages.ml_clients.vad.base import VADClientInterface
from chatzzk.packages.schemas.data_models import StreamContextEntry
from chatzzk.packages.schemas.db_models import ChzzkVodORM
from chatzzk.packages.utils.downloader import download_file_from_url
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)
from chatzzk.services.collector.settings import collector_settings

TARGET_INDEX_FOR_VIDEO_RESOLUTION = collector_settings.target_index_for_video_resolution


class VodProcessingService:
    """VOD 처리의 전체 파이프라인과 비즈니스 로직을 캡슐화합니다."""

    def __init__(
        self,
        db_session_provider: callable,
        chzzk_client: ChzzkPlatformClient,
        vad_client: VADClientInterface,
        asr_client: ASRClientInterface,
        storage_manager: StorageInterface,
    ):
        self.db_session_provider = db_session_provider
        self.chzzk_client = chzzk_client
        self.vad_client = vad_client
        self.asr_client = asr_client
        self.storage_manager = storage_manager
        self.paths = None  # 임시 경로 객체를 저장할 인스턴스 변수

    def process(self, vod_pk: int) -> str:
        """주어진 VOD PK에 대한 전체 처리 파이프라인을 실행합니다."""
        video_no, status_details = self._initialize_and_get_status(vod_pk)
        self.paths = self._prepare_workspace(video_no)

        try:
            # 각 단계를 순차적으로 실행
            self._step_crawl_chat(video_no, status_details)
            self._step_download_video(video_no, status_details)
            self._step_extract_wav(video_no, status_details)
            self._step_perform_asr(video_no, status_details)
            self._step_merge_and_upload(vod_pk, video_no, status_details)

            self._cleanup_workspace(video_no)
            return f"Successfully processed VOD {vod_pk}"

        except Exception as e:
            logger.opt(exception=True).error(f"❌ Error during VOD processing for {video_no}: {e}")
            # 실패 시에도 안전하게 상태 업데이트
            with self.db_session_provider() as db:
                vod_repo = VodRepository(db)
                vod_to_fail = vod_repo.get_by_pk(vod_pk)
                if vod_to_fail:
                    vod_repo.update_process_status(vod_to_fail, VodProcessStatus.FAILED)
                    db.commit()
            raise  # Celery Task가 재시도할 수 있도록 예외를 다시 발생시킴

    # --- Private Helper Methods for each step ---

    def _initialize_and_get_status(self, vod_pk: int) -> tuple[str, dict]:
        """초기 DB 조회를 수행하고 처리 상태를 'PROCESSING'으로 업데이트합니다."""
        with self.db_session_provider() as db:
            vod_repo = VodRepository(db)
            vod = vod_repo.get_by_pk(vod_pk)
            if not vod:
                raise ValueError(f"VOD with id {vod_pk} not found.")  # 재시도 불가능한 에러

            video_no = vod.video_no
            status_details = vod.status_details or {}
            logger.info(f"🚀 Starting VOD processing for vod_pk: {vod_pk} (video_no: {video_no})")
            vod_repo.update_process_status(vod, VodProcessStatus.PROCESSING)
            db.commit()
        return video_no, status_details

    def _step_crawl_chat(self, video_no: str, status: dict):
        if status.get(PipelineStep.CRAWL_CHAT, {}).get(PipelineStep.STATUS_KEY) == StepStatus.COMPLETED:
            return
        logger.info(f"[{video_no}] Step: Crawling chat data...")
        chat_contexts = self.chzzk_client.crawl_chat(video_no)
        with open(self.paths.chat_context, "w", encoding="utf-8") as f:
            for entry in chat_contexts:
                f.write(entry.model_dump_json() + "\n")
        self._update_pipeline_step(video_no, PipelineStep.CRAWL_CHAT)

    def _step_download_video(self, video_no: str, status: dict):
        if status.get(PipelineStep.DOWNLOAD_VIDEO, {}).get(PipelineStep.STATUS_KEY) == StepStatus.COMPLETED:
            return
        logger.info(f"[{video_no}] Step: Downloading video...")
        details = self.chzzk_client.fetch_vod_details(video_no)
        _, video_id, in_key = details
        stream_reps = self.chzzk_client.fetch_all_stream_representations(video_id, in_key)
        download_url = stream_reps[TARGET_INDEX_FOR_VIDEO_RESOLUTION][1]
        download_file_from_url(url=download_url, destination_path=self.paths.mp4, session=self.chzzk_client.session)
        self._update_pipeline_step(video_no, PipelineStep.DOWNLOAD_VIDEO)

    def _step_extract_wav(self, video_no: str, status: dict):
        if status.get(PipelineStep.EXTRACT_WAV, {}).get(PipelineStep.STATUS_KEY) == StepStatus.COMPLETED:
            return
        logger.info(f"[{video_no}] Step: Extracting WAV from video...")
        extract_wav_from_video(self.paths.mp4, self.paths.wav)
        self._update_pipeline_step(video_no, PipelineStep.EXTRACT_WAV)

    def _step_perform_asr(self, video_no: str, status: dict):
        if status.get(PipelineStep.PERFORM_ASR, {}).get(PipelineStep.STATUS_KEY) == StepStatus.COMPLETED:
            return
        logger.info(f"[{video_no}] Step: Performing VAD and ASR...")
        audio_np, sr = load_audio(self.paths.wav)
        timestamps = self.vad_client.detect_speech(audio_np)
        asr_context = self._perform_asr_and_create_context(self.asr_client, audio_np, timestamps, sr)
        with open(self.paths.asr_context, "w", encoding="utf-8") as f:
            for entry in asr_context:
                f.write(entry.model_dump_json() + "\n")
        self._update_pipeline_step(video_no, PipelineStep.PERFORM_ASR)

    def _step_merge_and_upload(self, vod_pk: int, video_no: str, status: dict):
        if status.get(PipelineStep.MERGE_AND_UPLOAD, {}).get(PipelineStep.STATUS_KEY) == StepStatus.COMPLETED:
            return
        logger.info(f"[{video_no}] Step: Merging context and uploading to storage...")
        merged_context = merge_context_files(self.paths.chat_context, self.paths.asr_context)
        context_file_key = self.storage_manager.save_context(video_no, merged_context)
        if context_file_key:
            with self.db_session_provider() as db:
                analysis_repo = AnalysisResultRepository(db)
                vod_repo = VodRepository(db)
                vod = vod_repo.get_by_pk(vod_pk)
                result_data = {AnalysisResultKey.CONTEXT_FILE_KEY: context_file_key}
                analysis_repo.create(vod, result_data)
                self._update_pipeline_step_in_db(db, vod, PipelineStep.MERGE_AND_UPLOAD, commit=False)
                db.commit()

    def _update_pipeline_step(self, video_no: str, step: str):
        """단일 파이프라인 단계의 완료 상태를 DB에 기록합니다."""
        with self.db_session_provider() as db:
            vod_repo = VodRepository(db)
            vod = vod_repo.get_by_video_no(video_no)
            self._update_pipeline_step_in_db(db, vod, step)

    def _update_pipeline_step_in_db(self, db: Session, vod: ChzzkVodORM, step: str, commit: bool = True):
        """주어진 DB 세션 내에서 파이프라인 단계를 업데이트합니다."""
        if vod:
            VodRepository(db).update_pipeline_step(vod, step, StepStatus.COMPLETED)
            if commit:
                db.commit()

    # --- Workspace and ASR context methods (moved from module level) ---
    def _prepare_workspace(self, video_no: str):
        base_dir = Path(collector_settings.workspace_base_dir)
        workspace_dir = base_dir / video_no
        workspace_dir.mkdir(parents=True, exist_ok=True)

        class Paths:
            mp4, wav, chat_context, asr_context = (
                workspace_dir / f for f in (TempFile.VIDEO, TempFile.AUDIO, TempFile.CHAT_CONTEXT, TempFile.ASR_CONTEXT)
            )

        logger.info(f"[{video_no}] Prepared temporary workspace at: {workspace_dir}")
        return Paths()

    def _cleanup_workspace(self, video_no: str):
        base_dir = Path(collector_settings.workspace_base_dir)
        workspace_dir = base_dir / video_no
        if workspace_dir.exists():
            try:
                shutil.rmtree(workspace_dir)
                logger.info(f"[{video_no}] Cleaned up temporary workspace: {workspace_dir}")
            except OSError as e:
                logger.error(f"Failed to clean up workspace {workspace_dir}: {e}")

    def _perform_asr_and_create_context(self, asr_client, audio_np, timestamps, sample_rate=16000):
        # (기존 _perform_asr_and_create_context 로직과 동일)
        asr_context_entries = []
        logger.info(f"Performing ASR on {len(timestamps)} audio segments...")
        for start_sample, end_sample in timestamps:
            segment_audio = audio_np[start_sample:end_sample]
            transcription_text = asr_client.transcribe(segment_audio)
            if transcription_text:
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
