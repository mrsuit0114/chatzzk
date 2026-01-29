from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.ml.audio_loader import AudioLoader
from chatzzk_clients.ml.vad import VADClientInterface
from chatzzk_core.constants import AudioDataConstant, StoragePaths, VODPipelineStepStatus, VODProcessingStep
from chatzzk_data_access.repositories import VODRepository
from chatzzk_data_access.storages import LocalStorage


class VADService(BasePipelineService):
    CHUNK_DURATION_S = AudioDataConstant.CHUNK_DURATION_S
    MAX_SPEECH_SAMPLES = AudioDataConstant.MAX_SPEECH_DURATION_S * AudioDataConstant.SAMPLE_RATE
    MIN_SILENCE_DURATION_SAMPLES = AudioDataConstant.MIN_SILENCE_DURATION_MS * AudioDataConstant.SAMPLE_RATE // 1000

    def __init__(
        self,
        audio_loader: AudioLoader,
        vod_repo: VODRepository,
        vad_client: VADClientInterface,
        tmp_storage: LocalStorage,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(vod_repo, db_session_factory)
        self.audio_loader = audio_loader
        self.vad_client = vad_client
        self.tmp_storage = tmp_storage

    async def perform_vad(self, vod_id: int) -> str:
        start_at = self._get_utc_now()
        step_status = VODPipelineStepStatus.FAILED
        pipeline_step = VODProcessingStep.PERFORM_VAD

        audio_key = StoragePaths.get_audio_key(vod_id=vod_id)
        vad_timestamps_key = StoragePaths.get_vad_timestamps_key(vod_id=vod_id)

        if await self._is_step_completed(vod_id, pipeline_step):
            return vad_timestamps_key

        try:
            audio_path = self.tmp_storage.get_absolute_path(audio_key)
            speech_timestamps = await self._run_vad_streaming(audio_path)

            vad_key = await self.tmp_storage.write_jsonl(vad_timestamps_key, speech_timestamps)

            step_status = VODPipelineStepStatus.COMPLETED
            return vad_key

        except Exception as e:
            logger.error(f"Failed to perform VAD for vod_id={vod_id}: {e}")
            await self._fail_pipeline(vod_id)
            raise
        finally:
            await self._record_step_status(vod_id, pipeline_step, step_status, start_at, self._get_utc_now())

    async def _run_vad_streaming(self, audio_path: str) -> list[dict]:
        """
        [Core Logic] 오디오를 스트리밍 방식으로 읽어 VAD를 수행하고 결과를 병합합니다.
        """
        # 1. 디코더 준비 (메타데이터 로드)
        decoder = self.audio_loader.get_decoder(audio_path)
        total_duration = decoder.metadata.duration_seconds

        all_timestamps = []
        current_time = 0.0

        while current_time < total_duration:
            end_time = min(current_time + self.CHUNK_DURATION_S, total_duration)

            # 2. 청크 디코딩 & 추론
            chunk_results = await self._process_single_chunk(decoder, current_time, end_time)

            # 3. 결과 병합 (Stitching)
            self._merge_chunk_results(all_timestamps, chunk_results, current_time)

            current_time += self.CHUNK_DURATION_S

        return all_timestamps

    async def _process_single_chunk(self, decoder, start_time: float, end_time: float) -> list[dict]:
        """단일 청크를 디코딩하고 VAD 클라이언트에 추론을 요청합니다."""
        chunk_samples = decoder.get_samples_played_in_range(start_seconds=start_time, stop_seconds=end_time)
        chunk_np = self.audio_loader.to_numpy(chunk_samples)

        # Client 호출 (Stateless)
        return await self.vad_client.detect_speech(chunk_np)

    def _merge_chunk_results(self, all_timestamps: list[dict], chunk_results: list[dict], current_time_offset: float):
        """
        청크 단위 VAD 결과를 전체 타임스탬프 리스트에 병합합니다.
        - 시간 오프셋 적용
        - 경계면 병합 (조건부)
        - 최대 길이 제한 체크
        """
        offset_samples = int(current_time_offset * AudioDataConstant.SAMPLE_RATE)

        for segment in chunk_results:
            abs_start = segment["start"] + offset_samples
            abs_end = segment["end"] + offset_samples

            merged = False

            # 이전 세그먼트와 병합 시도
            if all_timestamps:
                prev_seg = all_timestamps[-1]
                silence_gap = abs_start - prev_seg["end"]

                # [조건 1] 이어지는 음성인가?
                if silence_gap <= self.MIN_SILENCE_DURATION_SAMPLES:
                    new_duration = abs_end - prev_seg["start"]

                    # [조건 2] 30초 제한 준수 확인
                    if new_duration <= self.MAX_SPEECH_SAMPLES:
                        prev_seg["end"] = abs_end
                        merged = True

            if not merged:
                all_timestamps.append({"start": abs_start, "end": abs_end})
