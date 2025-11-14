from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk.packages.clients.media.media_processor import MediaProcessor
from chatzzk.packages.clients.ml.asr.base import ASRClientInterface
from chatzzk.packages.clients.ml.vad.base import VADClientInterface
from chatzzk.packages.constants.service_codes import FileKeyTemplate, VODProcessingStep, VODProcessingStepStatus
from chatzzk.packages.data_access.repositories.vod import VODRepository
from chatzzk.packages.data_access.storages.base import PipelineStorage
from chatzzk.packages.schemas.dto.api.core.vod import (
    ASRPerformRequestDTO,
    ASRPerformResponseDTO,
    VADPerformRequestDTO,
    VADPerformResponseDTO,
)
from chatzzk.packages.schemas.dto.repo_params.core.vod import get_vod_find_params
from chatzzk.packages.schemas.storage.models import ASREntry, VADTimestampEntry
from chatzzk.services.interfaces.speech_processing import SpeechProcessingInterface


class SpeechProcessingService(SpeechProcessingInterface):
    def __init__(
        self,
        tmp_storage: PipelineStorage,
        vod_repo: VODRepository,
        media_processor: MediaProcessor,
        db_session_factory: async_sessionmaker[AsyncSession],
        vad_client: VADClientInterface | None = None,
        asr_client: ASRClientInterface | None = None,
    ):
        self.tmp_storage = tmp_storage
        self.vod_repo = vod_repo
        self.media_processor = media_processor
        self.db_session_factory = db_session_factory
        self.vad_client = vad_client
        self.asr_client = asr_client

    async def perform_vad(self, dto: VADPerformRequestDTO) -> VADPerformResponseDTO:
        video_no = dto.video_no
        platform_code = dto.platform_code
        vad_timestamp_key = FileKeyTemplate.get_vad_timestamp_key(platform_code, video_no)

        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = get_vod_find_params(**dto.model_dump())
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(session, platform_code, vod_find_params)
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)
                detail = vod.vod_processing_status_detail.status_details or {}

        vad_done = detail.get(VODProcessingStep.PERFORM_VAD, {}).get("status") == VODProcessingStepStatus.COMPLETED
        if vad_done:
            return VADPerformResponseDTO(
                vad_timestamp_key=vad_timestamp_key, vad_result=VODProcessingStepStatus.COMPLETED
            )

        start_time = datetime.now(UTC)
        vad_status = VODProcessingStepStatus.FAILED

        try:
            audio_key = FileKeyTemplate.get_audio_key(platform_code, video_no)
            audio_path = self.tmp_storage.get_path(audio_key)
            audio_np, _ = self.media_processor.load_audio(audio_path)

            timestamps = await self.vad_client.detect_speech(audio_np)

            async def timestamps_generator():
                for timestamp in timestamps:
                    entry = VADTimestampEntry.from_vad_timestamp(timestamp)
                    yield entry.model_dump()

            await self.tmp_storage.save_jsonl(vad_timestamp_key, timestamps_generator())
            vad_status = VODProcessingStepStatus.COMPLETED
        except Exception as e:
            logger.error(f"perform vad failed {platform_code}, {video_no} : {e}")

        end_time = datetime.now(UTC)

        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = get_vod_find_params(**dto.model_dump())
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(session, platform_code, vod_find_params)
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)

                self.vod_repo.update_processing_detail(
                    session,
                    vod,
                    step=VODProcessingStep.PERFORM_VAD,
                    status=vad_status,
                    start_time=start_time,
                    end_time=end_time,
                )

        return VADPerformResponseDTO(vad_timestamp_key=vad_timestamp_key, vad_result=vad_status)

    async def perform_asr(self, dto: ASRPerformRequestDTO):
        video_no = dto.video_no
        platform_code = dto.platform_code
        asr_key = FileKeyTemplate.get_asr_key(platform_code, video_no)

        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = get_vod_find_params(**dto.model_dump())
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(session, platform_code, vod_find_params)
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)
                detail = vod.vod_processing_status_detail.status_details or {}

        asr_done = detail.get(VODProcessingStep.PERFORM_ASR, {}).get("status") == VODProcessingStepStatus.COMPLETED

        if asr_done:
            return ASRPerformResponseDTO(asr_key=asr_key, asr_result=VODProcessingStepStatus.COMPLETED)

        start_time = datetime.now(UTC)
        asr_status = VODProcessingStepStatus.FAILED

        try:
            audio_key = FileKeyTemplate.get_audio_key(platform_code, video_no)
            vad_timestamp_key = FileKeyTemplate.get_vad_timestamp_key(platform_code, video_no)

            timestamps = await self.tmp_storage.load_jsonl(vad_timestamp_key)
            audio_path = self.tmp_storage.get_path(audio_key)
            audio_np, sr = self.media_processor.load_audio(audio_path)
            asr_results = []

            async for raw_ts in timestamps:
                t = VADTimestampEntry.model_validate(raw_ts)
                start, end = t.start_sample, t.end_sample
                transcription = await self.asr_client.transcribe(audio_np[start:end])
                asr_results.append((start, end, transcription))
                logger.info(asr_results[-1])

            async def asr_results_generator():
                for start, end, transcription in asr_results:
                    entry = ASREntry.from_asr_result(start, end, transcription, sr)
                    yield entry.model_dump()

            await self.tmp_storage.save_jsonl(asr_key, asr_results_generator())
            asr_status = VODProcessingStepStatus.COMPLETED

        except Exception as e:
            logger.error(f"perform asr failed {platform_code}, {video_no} : {e}")

        end_time = datetime.now(UTC)

        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = get_vod_find_params(**dto.model_dump())
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(session, platform_code, vod_find_params)
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)

                self.vod_repo.update_processing_detail(
                    session,
                    vod,
                    step=VODProcessingStep.PERFORM_ASR,
                    status=asr_status,
                    start_time=start_time,
                    end_time=end_time,
                )

        return ASRPerformResponseDTO(asr_key=asr_key, asr_result=asr_status)
