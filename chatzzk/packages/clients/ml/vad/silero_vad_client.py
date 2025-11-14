import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np
import torch
from loguru import logger

from chatzzk.packages.clients.ml.exceptions import VADError
from chatzzk.packages.clients.ml.vad.base import VADClientInterface
from chatzzk.packages.schemas.config.clients.ml import SileroVADConfig

# --- 멀티프로세싱을 위한 최상위 레벨 함수 정의 ---


def init_vad_worker():
    """각 자식 프로세스에서 VAD 모델을 초기화하는 함수"""
    global vad_model
    torch.set_num_threads(1)
    from silero_vad import load_silero_vad

    logger.debug(f"Initializing VAD model in process {os.getpid()}...")
    vad_model = load_silero_vad(onnx=True)


def process_vad_chunk(
    audio_chunk_np: np.ndarray,
    threshold: float,
    min_silence_duration_ms: int,
    max_speech_duration_s: int,
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
        logger.error(f"VAD detection failed in process {os.getpid()}: {e}")
        raise VADError("VAD detection failed in worker process") from e


# --- SileroVADClient 클래스 --- VAD 작업 오케스트레이터


class SileroVADClient(VADClientInterface):
    def __init__(self, config: SileroVADConfig):
        self.config = config
        self.executor = ProcessPoolExecutor(max_workers=config.worker_num, initializer=init_vad_worker)
        logger.info(f"SileroVADClient initialized with ProcessPoolExecutor(worker_num={config.worker_num}).")

    def _split_audio(self, audio_np: np.ndarray) -> tuple[list[np.ndarray], list[int]]:
        total_len = len(audio_np)
        chunk_size = total_len // self.config.worker_num
        split_idxs = [i * chunk_size for i in range(self.config.worker_num)]
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
        for i in range(self.config.worker_num):
            start = chunk_start_by_chunk_samples[i]
            if i < self.config.worker_num - 1:
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
        combined_timestamps: list[dict[str, int]] = []

        for i, chunk_timestamps in enumerate(chunk_results):
            if not chunk_timestamps:
                continue

            chunk_start = chunk_starts[i]
            # 각 chunk의 결과를 dict로 변환하여 offset 적용
            chunk_segments = [
                {"start": ts["start"] + chunk_start, "end": ts["end"] + chunk_start} for ts in chunk_timestamps
            ]

            if not combined_timestamps:
                # 첫 chunk는 그대로 추가
                combined_timestamps.extend(chunk_segments)
                continue

            prev = combined_timestamps[-1]
            cur = chunk_segments[0]

            if cur["start"] - prev["end"] <= min_silence_samples:
                # 이전 segment와 병합
                combined_timestamps[-1] = {"start": prev["start"], "end": cur["end"]}
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
            logger.error(f"An error occurred during parallel VAD processing: {e}")
            raise VADError("Failed to execute VAD task in process pool") from e

    def close(self):
        """애플리케이션 종료 시 Executor를 안전하게 종료합니다."""
        logger.info("Shutting down VAD ProcessPoolExecutor...")
        self.executor.shutdown()
