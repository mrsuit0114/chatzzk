from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.ml.asr.base import ASRClientInterface
from chatzzk_clients.ml.audio_loader import AudioLoader
from chatzzk_core.constants.service_codes import AudioDataConstant, StoragePaths
from chatzzk_core.schemas.internal.models import ASREntry
from chatzzk_data_access.repositories.vod import VODRepository
from chatzzk_data_access.storages.local_storage import LocalStorage


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
        audio_key = StoragePaths.get_audio_key(vod_id)
        vad_key = StoragePaths.get_vad_timestamps_key(vod_id)
        asr_key = StoragePaths.get_asr_key(vod_id)

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

        # 4. 오디오 메모리 로드 (전체 로드 전략)
        audio_np, sr = self.audio_loader.load(audio_abs_path)

        if sr != self.target_sr:
            logger.warning(
                f"Sample rate mismatch: expected {self.target_sr}, got {sr}. ASR results might be inaccurate."
            )

        # 5. 순차 처리 (Sequential Processing)
        for idx, segment in enumerate(remaining_tasks):
            start_sample = segment["start"]
            end_sample = segment["end"]

            chunk_np = audio_np[start_sample:end_sample]

            # ASR 추론 요청
            try:
                text = await self.asr_client.transcribe(chunk_np)
            except Exception as e:
                logger.error(f"❌ ASR failed at segment {processed_count + idx} (start={start_sample}): {e}")
                raise

            entry = ASREntry(
                start=int(start_sample / self.target_sr * 1000),
                end=int(end_sample / self.target_sr * 1000),
                timestamp=int((end_sample + start_sample) / 2 / self.target_sr * 1000),
                content=text,
            )

            await self.tmp_storage.append_jsonl(asr_key, entry.model_dump())

        logger.info(f"✅ ASR completed for vod_id={vod_id}. Saved to {asr_key}")
        return asr_key
