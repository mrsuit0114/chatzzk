import queue
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from time import time

import numpy as np
from context.audio.asr import ASR
from context.audio.circular_audio_buffer import CircularAudioBuffer
from context.audio.vad import VAD
from data_types.context_data import ContextData
from loguru import logger


class AudioProcessor:
    """
    Periodically retrieves audio from the buffer, runs VAD and ASR, and stores results in context_audio_deque.
    Since both processing and storage involve threads, separating them would increase complexity due to locking and synchronization.
    Therefore, this class encapsulates both processing and storage to simplify thread management.
    """

    def __init__(self, config: dict, audio_buffer: CircularAudioBuffer, shared_config: dict):
        self.audio_buffer = audio_buffer
        self.target_sampling_rate: int = config["target_sampling_rate"]
        self.bytes_per_sample: int = config["bytes_per_sample"]
        self.min_silence_duration_ms: int = config["min_silence_duration_ms"]
        self.max_speech_duration_ms: int = config["max_speech_duration_ms"]
        self.sample_to_ms: float = 1000 / self.target_sampling_rate / self.bytes_per_sample
        self.offset_ms = config["offset_ms"]
        self.prompt_cmd_to_type_code = shared_config["prompt_cmd_to_type_code"]
        self.type_code_to_prompt_cmd = {v: k.upper() for k, v in self.prompt_cmd_to_type_code.items()}

        self.vad = VAD(self.min_silence_duration_ms, self.max_speech_duration_ms // 1000)
        self.asr = ASR(config["model_size"], config["not_expected_asr_list"])

        self.asr_history: deque[ContextData] = deque()
        self.asr_history_lock = threading.Lock()

        # 실행시간이 긴 ASR은 비동기로 수행하고 Queue를 관리하여 순서를 보장
        self.is_running = False
        self.stop_event = threading.Event()

        self.asr_queue = queue.Queue()
        self.asr_thread = threading.Thread(target=self._asr_worker)
        self.asr_thread.daemon = True

        self.model_inference_interval_s: int = config["model_inference_interval_s"]
        self.inference_scheduler_executor = ThreadPoolExecutor(max_workers=3)
        self.inference_scheduler_thread = threading.Thread(target=self._inference_scheduler_loop)
        self.inference_scheduler_thread.daemon = True

        self.threads = [self.asr_thread, self.inference_scheduler_thread]

    def run(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()
        for thread in self.threads:
            thread.start()

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

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"[Processor] {thread.name} stopped.")

        self.inference_scheduler_executor.shutdown(wait=True)

    def _get_timestamps(self, audio_data: np.ndarray) -> list[tuple[int, int]]:
        return self.vad(audio_data)

    def _get_asr_results(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]) -> list[str]:
        return self.asr(audio_data, timestamps)

    def _asr_worker(self) -> None:
        """Background thread function that processes ASR tasks from the queue."""
        while not self.stop_event.is_set():
            try:
                audio_data_np, timestamps, snapshot_timestamp_ms = self.asr_queue.get(timeout=1.0)

                asr_results = self._get_asr_results(audio_data_np, timestamps)
                logger.info(f"[ASR Worker] Results: {asr_results}")

                with self.asr_history_lock:
                    for timestamp, result in zip(timestamps, asr_results):
                        speech_length = timestamp[1] - timestamp[0]
                        speech_time_ms = int(
                            snapshot_timestamp_ms - (speech_length // self.bytes_per_sample * self.sample_to_ms) // 2
                        )
                        speech_time_ms -= self.offset_ms
                        type_code = self.prompt_cmd_to_type_code["asr"]
                        prompt_str = f"[{self.type_code_to_prompt_cmd[type_code]}] {result}\n"
                        self.asr_history.append(ContextData(speech_time_ms, result, type_code, prompt_str))

                self.asr_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[ASR Worker] Error processing ASR: {e}")
                continue

    def _process_asr_results(self, audio_data_np: np.ndarray, timestamps: list[tuple[int, int]]) -> None:
        snapshot_timestamp_ms = int(time() * 1000)
        self.asr_queue.put((audio_data_np, timestamps, snapshot_timestamp_ms))

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

        audio_data = self.audio_buffer.get_all_data()
        start_idx = self.audio_buffer.get_last_speech_timestamp_idx()

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
                    self.audio_buffer.update_last_speech_timestamp_idx(self.bytes_per_sample * last_timestamp[0])
                    if len(timestamps) > 1:
                        timestamps = timestamps[:-1]
                        self._process_asr_results(audio_data_np, timestamps)
                else:
                    self.audio_buffer.update_last_speech_timestamp_idx(self.bytes_per_sample * last_timestamp[1])
                    self._process_asr_results(audio_data_np, timestamps)
            else:
                self.audio_buffer.update_last_speech_timestamp_idx(len(audio_data))
        except Exception as e:
            logger.error(f"[Model Inference Task] Error during inference: {e}")

    def _inference_scheduler_loop(self) -> None:
        while self.is_running and not self.stop_event.is_set():
            self.inference_scheduler_executor.submit(self._perform_model_inference_task)
            if self.stop_event.wait(self.model_inference_interval_s):
                break

    def get_new_asr_results(self) -> list[ContextData]:
        with self.asr_history_lock:
            latest_asr = list(self.asr_history)
            self.asr_history.clear()
        return latest_asr
