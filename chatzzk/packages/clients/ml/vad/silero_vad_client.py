import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np
import torch
from loguru import logger

from chatzzk.packages.clients.ml.exceptions import VadError
from chatzzk.packages.clients.ml.vad.base import VadClientInterface
from chatzzk.packages.constants.service_codes import MAX_SPEECH_DURATION_S, MIN_SILENCE_DURATION_MS
from chatzzk.packages.schemas.config.ml import SileroVadConfig

# --- 멀티프로세싱을 위한 최상위 레벨 함수 정의 ---


def init_vad_worker():
    """각 자식 프로세스에서 Vad 모델을 초기화하는 함수"""
    global vad_model
    torch.set_num_threads(1)
    from silero_vad import load_silero_vad

    logger.debug(f"Initializing Vad model in process {os.getpid()}...")
    vad_model = load_silero_vad(onnx=True)


def process_vad_chunk(
    audio_chunk_np: np.ndarray,
    threshold: float,
    min_silence_duration_ms: int = MIN_SILENCE_DURATION_MS,
    max_speech_duration_s: int = MAX_SPEECH_DURATION_S,
) -> list[tuple[int, int]]:
    """자식 프로세스에서 단일 오디오 조각을 처리하는 실제 작업 함수"""
    global vad_model
    from silero_vad import get_speech_timestamps

    try:
        audio_chunk_ts = torch.from_numpy(audio_chunk_np)
        speech_timestamps = get_speech_timestamps(
            audio_chunk_ts,
            vad_model,
            min_silence_duration_ms=min_silence_duration_ms,
            max_speech_duration_s=max_speech_duration_s,
            threshold=threshold,
        )
        return speech_timestamps
    except Exception as e:
        logger.error(f"Vad detection failed in process {os.getpid()}: {e}")
        raise VadError("Vad detection failed in worker process") from e


# --- SileroVadClient 클래스 --- Vad 작업 오케스트레이터


class SileroVadClient(VadClientInterface):
    def __init__(self, config: SileroVadConfig):
        self.config = config
        self.executor = ProcessPoolExecutor(max_workers=config.max_workers, initializer=init_vad_worker)
        logger.info(f"SileroVadClient initialized with ProcessPoolExecutor(max_workers={config.max_workers}).")

    def _split_audio(self, audio_np: np.ndarray) -> tuple[list[np.ndarray], list[int]]:
        total_len = len(audio_np)
        chunk_size = total_len // self.config.max_workers
        split_idxs = [i * chunk_size for i in range(self.config.max_workers)]
        # split_idxs의 각 값에 대해, 해당 값보다 작거나 같은 self.config.sample_chunk_size의 배수 중 가장 큰 값을 구함
        chunk_start_by_chunk_samples = []
        for idx in split_idxs:
            if idx < self.config.sample_chunk_size:
                chunk_start_by_chunk_samples.append(0)
            else:
                chunk_start_by_chunk_samples.append(
                    (idx // self.config.sample_chunk_size) * self.config.sample_chunk_size
                )

        chunks = []
        for i in range(self.config.max_workers):
            start = chunk_start_by_chunk_samples[i]
            if i < self.config.max_workers - 1:
                end = chunk_start_by_chunk_samples[i + 1] + self.config.overlap_num * self.config.sample_chunk_size
                end = min(end, total_len)
            else:
                end = total_len
            chunk = audio_np[start:end]
            chunks.append(chunk)
        return (chunks, chunk_start_by_chunk_samples)

    def _combine_chunk_timestamps(
        self, chunk_results: list[list[dict[str, int]]], chunk_starts: list[int], min_silence_samples: int
    ):
        # chunk_timestamps: _split_audio에서 구한 chunks에 대해 timestamps의 리스트 list[list[dict[str, int]]]
        combined_timestamps = []

        for i, chunk_timestamps in enumerate(chunk_results):
            if not chunk_timestamps:
                continue

            chunk_start = chunk_starts[i]
            chunk_segments = [(ts["start"] + chunk_start, ts["end"] + chunk_start) for ts in chunk_timestamps]

            if not combined_timestamps:
                # 첫 chunk는 그대로 추가
                combined_timestamps.extend(chunk_segments)
                continue

            prev_start, prev_end = combined_timestamps[-1]
            cur_start, cur_end = chunk_segments[0]

            if cur_start - prev_end <= min_silence_samples:
                combined_timestamps[-1] = (prev_start, cur_end)
                combined_timestamps.extend(chunk_segments[1:])
            else:
                combined_timestamps.extend(chunk_segments)

        return combined_timestamps

    async def detect_speech(self, audio_np: np.ndarray) -> list[tuple[int, int]]:
        audio_chunks, chunk_start_by_chunk_samples = self._split_audio(audio_np)

        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(
                self.executor,
                partial(
                    process_vad_chunk,
                    audio_chunk_np=chunk,
                    min_silence_duration_ms=self.config.min_silence_duration_ms,
                    max_speech_duration_s=self.config.max_speech_duration_s,
                    threshold=self.config.threshold,
                ),
            )
            for chunk in audio_chunks
        ]

        try:
            chunk_results = await asyncio.gather(*tasks)
            return self._combine_chunk_timestamps(
                chunk_results, chunk_start_by_chunk_samples, self.config.min_silence_duration_samples
            )
        except Exception as e:
            logger.error(f"An error occurred during parallel Vad processing: {e}")
            raise VadError("Failed to execute Vad task in process pool") from e

    def close(self):
        """애플리케이션 종료 시 Executor를 안전하게 종료합니다."""
        logger.info("Shutting down Vad ProcessPoolExecutor...")
        self.executor.shutdown()
