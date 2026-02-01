from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.ml.asr import ASRClientInterface
from chatzzk_clients.ml.audio_loader import AudioLoader
from chatzzk_core.constants import AudioDataConstant, StoragePaths, VODPipelineStepStatus, VODProcessingStep
from chatzzk_core.schemas.internal import ASREntry
from chatzzk_data_access.repositories import VODRepository
from chatzzk_data_access.storages import LocalStorage


class ASRService(BasePipelineService):
    def __init__(
        self,
        audio_loader: AudioLoader,
        vod_repo: VODRepository,
        asr_client: ASRClientInterface,
        tmp_storage: LocalStorage,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(vod_repo, db_session_factory)
        self.audio_loader = audio_loader
        self.asr_client = asr_client
        self.tmp_storage = tmp_storage
        self.target_sr = AudioDataConstant.SAMPLE_RATE

    async def perform_asr(self, vod_id: int) -> str:
        """
        VAD 타임스탬프를 기반으로 오디오를 잘라 ASR 서버에 요청하고 결과를 저장합니다.
        중단된 작업이 있을 경우 이어서 수행합니다 (Resume).
        """
        start_at = self._get_utc_now()
        step_status = VODPipelineStepStatus.FAILED
        pipeline_step = VODProcessingStep.PERFORM_ASR

        audio_key = StoragePaths.get_audio_key(vod_id)
        vad_key = StoragePaths.get_vad_timestamps_key(vod_id)
        asr_key = StoragePaths.get_asr_key(vod_id)

        if await self._is_step_completed(vod_id, pipeline_step):
            return asr_key

        try:
            audio_abs_path = self.tmp_storage.get_absolute_path(audio_key)

            # 2. [Resume Logic] 기존 진행 상황 파악
            processed_count = await self.tmp_storage.count_jsonl_lines(asr_key)

            # 3. VAD 타임스탬프 로드
            try:
                vad_entries = await self.tmp_storage.read_jsonl(vad_key)
            except FileNotFoundError:
                logger.error(f"VAD timestamps not found for vod_id={vod_id}")
                raise

            # 이미 처리된 개수만큼 스킵
            remaining_tasks = vad_entries[processed_count:]

            if not remaining_tasks:
                logger.info(f"✅ ASR already completed for vod_id={vod_id}")
                return asr_key

            logger.info(
                f"🔄 Resuming ASR for vod_id={vod_id}. Total: {len(vad_entries)}, Skipped: {processed_count}, Remaining: {len(remaining_tasks)}"
            )

            decoder = self.audio_loader.get_decoder(audio_abs_path)

            # 5. 순차 처리 (Sequential Processing)
            for idx, segment in enumerate(remaining_tasks):
                # VAD 타임스탬프 (샘플 단위)
                start_sample = int(segment["start"])
                end_sample = int(segment["end"])

                # [중요] 샘플 -> 초(Seconds) 변환
                # torchcodec의 get_samples_played_in_range는 '초' 단위를 받습니다.
                start_sec = start_sample / self.target_sr
                stop_sec = end_sample / self.target_sr

                try:
                    # -------------------------------------------------------
                    # ✨ 핵심: 디스크에서 딱 이 구간만 읽어옴 (메모리 절약)
                    # -------------------------------------------------------
                    chunk_samples = decoder.get_samples_played_in_range(start_seconds=start_sec, stop_seconds=stop_sec)

                    chunk_np = self.audio_loader.to_numpy(chunk_samples)

                except Exception as decode_err:
                    logger.error(f"Failed to decode chunk {start_sec:.2f}s ~ {stop_sec:.2f}s: {decode_err}")
                    raise

                # ASR 추론 요청
                try:
                    text = await self.asr_client.transcribe(chunk_np)
                except Exception as e:
                    logger.error(f"❌ ASR failed at segment {processed_count + idx}: {e}")
                    raise

                entry = ASREntry(
                    start=int(start_sample / self.target_sr * 1000),
                    end=int(end_sample / self.target_sr * 1000),
                    timestamp=int((end_sample + start_sample) / 2 / self.target_sr * 1000),
                    content=text,
                )

                await self.tmp_storage.append_jsonl(asr_key, entry.model_dump())

            logger.info(f"✅ ASR completed for vod_id={vod_id}. Saved to {asr_key}")
            step_status = VODPipelineStepStatus.COMPLETED
            return asr_key
        except Exception as e:
            logger.error(f"❌ Failed to perform ASR for vod_id={vod_id}: {e}")
            await self._fail_pipeline(vod_id)
            raise
        finally:
            await self._record_step_status(vod_id, pipeline_step, step_status, start_at, self._get_utc_now())
