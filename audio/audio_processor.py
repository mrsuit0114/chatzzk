import queue
import threading
from collections import deque
from time import time

import numpy as np
from loguru import logger

from audio.asr import ASR
from audio.circular_audio_buffer import CircularAudioBuffer
from audio.vad import VAD
from data_types.context_data import ContextData


class AudioProcessor:
    """
    Periodically retrieves audio from the buffer, runs VAD and ASR, and stores results in context_audio_deque.
    Since both processing and storage involve threads, separating them would increase complexity due to locking and synchronization.
    Therefore, this class encapsulates both processing and storage to simplify thread management.
    """

    def __init__(self, config: dict, audio_buffer: CircularAudioBuffer):
        self.audio_buffer = audio_buffer
        self.target_sampling_rate: int = config["target_sampling_rate"]
        self.bytes_per_sample: int = config["bytes_per_sample"]
        self.min_silence_duration_ms: int = config["min_silence_duration_ms"]
        self.max_speech_duration_ms: int = config["max_speech_duration_ms"]
        self.sample_to_ms: float = 1000 / self.target_sampling_rate / self.bytes_per_sample

        self.vad = VAD(self.min_silence_duration_ms, self.max_speech_duration_ms // 1000)
        self.asr = ASR(config["model_size"])

        self.audio_buffer_last_speech_timestamp_idx = 0
        self.audio_buffer_last_speech_timestamp_idx_lock = threading.Lock()

        self.context_audio_deque: deque[ContextData] = deque()
        self.context_audio_deque_lock = threading.Lock()

        # 실행시간이 긴 ASR은 비동기로 수행하고 Queue를 관리하여 순서를 보장
        self.asr_queue = queue.Queue()
        self.asr_thread = threading.Thread(target=self._asr_worker)
        self.asr_thread.daemon = True

        self.is_running = False
        self.stop_event = threading.Event()

        self.model_inference_interval_s: int = config["model_inference_interval_s"]
        self.model_inference_timer = None
        self.audio_context_duration_ms: int = config["audio_context_duration_ms"]

    def start(self) -> None:
        self.is_running = True
        self.stop_event.clear()
        self.asr_thread.start()
        self._schedule_model_inference_task()

    def stop(self) -> None:
        if not self.is_running:
            return
        logger.info("[Processor] Stopping AudioProcessor...")
        self.is_running = False
        self.stop_event.set()

        # Clear ASR queue
        while not self.asr_queue.empty():
            try:
                self.asr_queue.get_nowait()
                self.asr_queue.task_done()
            except queue.Empty:
                break

        if self.asr_thread.is_alive():
            self.asr_thread.join(timeout=5)
            logger.info("[Processor] ASR worker thread stopped.")

        if self.model_inference_timer:
            self.model_inference_timer.cancel()
            logger.info("[Processor] Model inference timer cancelled.")

    def _get_timestamps(self, audio_data: np.ndarray) -> list[tuple[int, int]]:
        return self.vad(audio_data)

    def _get_asr_results(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]) -> list[str]:
        return self.asr(audio_data, timestamps)

    def _asr_worker(self) -> None:
        """Background thread function that processes ASR tasks from the queue."""
        while not self.stop_event.is_set():
            try:
                audio_data_np, timestamps, start_idx, snapshot_timestamp_ms = self.asr_queue.get(timeout=1.0)

                asr_results = self._get_asr_results(audio_data_np, timestamps)
                logger.info(f"[ASR Worker] Results: {asr_results}")

                with self.context_audio_deque_lock:
                    for timestamp, result in zip(timestamps, asr_results):
                        start_time = (
                            snapshot_timestamp_ms
                            + (timestamp[0] + start_idx // self.bytes_per_sample) * self.sample_to_ms
                        )
                        end_time = (
                            snapshot_timestamp_ms
                            + (timestamp[1] + start_idx // self.bytes_per_sample) * self.sample_to_ms
                        )
                        middle_time = int((start_time + end_time) / 2)
                        self.context_audio_deque.append(ContextData(middle_time, result, "ASR"))

                self.asr_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[ASR Worker] Error processing ASR: {e}")
                continue

    def _process_asr_results(
        self, audio_data_np: np.ndarray, timestamps: list[tuple[int, int]], start_idx: int
    ) -> None:
        snapshot_timestamp_ms = int(time() * 1000)
        self.asr_queue.put((audio_data_np, timestamps, start_idx, snapshot_timestamp_ms))

    def _perform_model_inference_task(self) -> None:
        """Perform inference by extracting audio from buffer and applying VAD + ASR.

        Note:
            1. To avoid redundant ASR processing, we consider whether the last VAD segment might be incomplete by
                comparing it against the minimum silence duration (min_silence_duration_ms).
            2. If the last segment may continue, the next inference will start from the beginning of the last VAD segment.
            3. If there is no need to check the next segment, we simply advance by the length of the processed data.
        """
        if self.stop_event.is_set():
            logger.info("[Model Inference Task] Stop event set, exiting.")
            return

        # Update last_speech_timestamp_idx based on written bytes
        written_bytes = self.audio_buffer.get_and_reset_written_bytes()
        with self.audio_buffer_last_speech_timestamp_idx_lock:
            self.audio_buffer_last_speech_timestamp_idx = max(
                0, self.audio_buffer_last_speech_timestamp_idx - written_bytes
            )

        audio_data = self.audio_buffer.get_all_data()
        with self.audio_buffer_last_speech_timestamp_idx_lock:
            start_idx = self.audio_buffer_last_speech_timestamp_idx

        audio_data = audio_data[start_idx:]
        if len(audio_data) % 2 != 0:
            audio_data = audio_data[:-1]
        if not audio_data:
            logger.info("[Model Inference Task] No audio data available, skipping inference.")
            return

        audio_data_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            timestamps = self._get_timestamps(audio_data_np)
            if timestamps:
                last_timestamp = timestamps[-1]
                if last_timestamp[1] + int(self.min_silence_duration_ms / self.sample_to_ms) >= len(audio_data_np):
                    with self.audio_buffer_last_speech_timestamp_idx_lock:
                        self.audio_buffer_last_speech_timestamp_idx += self.bytes_per_sample * last_timestamp[0]
                    if len(timestamps) > 1:
                        timestamps = timestamps[:-1]
                        self._process_asr_results(audio_data_np, timestamps, start_idx)
                else:
                    with self.audio_buffer_last_speech_timestamp_idx_lock:
                        self.audio_buffer_last_speech_timestamp_idx += self.bytes_per_sample * last_timestamp[1]
                    self._process_asr_results(audio_data_np, timestamps, start_idx)
            else:
                with self.audio_buffer_last_speech_timestamp_idx_lock:
                    self.audio_buffer_last_speech_timestamp_idx += len(audio_data)
        except Exception as e:
            logger.error(f"[Model Inference Task] Error during inference: {e}")

    def _schedule_model_inference_task(self) -> None:
        if self.stop_event.is_set():
            logger.info("[Model Inference Task] Stop event set, exiting.")
            return

        self._perform_model_inference_task()

        if self.is_running and not self.stop_event.is_set():
            self.model_inference_timer = threading.Timer(
                self.model_inference_interval_s, self._schedule_model_inference_task
            )
            self.model_inference_timer.start()
        else:
            logger.info("[Processor Scheduler] Application stopping, timer not restarted.")

    def get_context_audio(self) -> list[ContextData]:
        """Assumes periodic invocation and is responsible for removing outdated data."""
        current_time = int(time() * 1000)
        with self.context_audio_deque_lock:
            while (
                self.context_audio_deque
                and self.context_audio_deque[0][0] < current_time - self.audio_context_duration_ms
            ):
                self.context_audio_deque.popleft()
            return list(self.context_audio_deque)
