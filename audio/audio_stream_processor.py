import queue
import threading
from collections import deque
from time import time

import ffmpeg
import numpy as np

from audio.asr import ASR
from audio.circular_audio_buffer import CircularAudioBuffer
from audio.vad import VAD

TARGET_SAMPLING_RATE = 16000
BUFFER_DURATION = 30  # 30 seconds buffer
BYTES_PER_SAMPLE = 2
MAX_BUFFER_SIZE = TARGET_SAMPLING_RATE * BYTES_PER_SAMPLE * BUFFER_DURATION
SAMPLE_TO_MS = 1000 / TARGET_SAMPLING_RATE / BYTES_PER_SAMPLE
AUDIO_CONTEXT_DURATION_MS = 40000

# 2초마다 모델 추론을 수행하도록 설정
MODEL_INFERENCE_INTERVAL_SECONDS = 2
FFMPEG_READ_CHUNK_SIZE = 4096  # ffmpeg stdout에서 한 번에 읽어올 청크 크기 (바이트)


class AudioStreamProcessor:
    """요청한 시점에 context에 포함될 오디오 데이터를 반환해야함
    [(ms, content), ... ]
    """

    def __init__(self, min_silence_duration_ms: int = 500, max_speech_duration_ms: int = 30000):
        self.m3u8_url: str = ""
        self.process = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.min_silence_duration_ms = min_silence_duration_ms
        self.max_speech_duration_ms = max_speech_duration_ms

        self.vad = VAD(min_silence_duration_ms, max_speech_duration_ms // 1000)
        self.asr = ASR()

        self.audio_buffer = CircularAudioBuffer(MAX_BUFFER_SIZE)
        self.audio_buffer_last_speech_timestamp_idx = 0
        self.audio_buffer_last_speech_timestamp_idx_lock = threading.Lock()

        self.context_audio_deque: deque[tuple[int, str]] = deque()
        self.context_audio_deque_lock = threading.Lock()

        self.model_inference_timer = None

        # ASR 처리를 위한 큐와 스레드
        self.asr_queue = queue.Queue()
        self.asr_thread = None

    def set_m3u8_url(self, m3u8_url: str):
        self.m3u8_url = m3u8_url

    def _get_timestamps(self, audio_data: np.ndarray):
        timestamps = self.vad(audio_data)
        return timestamps

    def _get_asr_results(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
        asr_results = self.asr(audio_data, timestamps)
        return asr_results

    def _asr_worker(self):
        """ASR 처리를 위한 워커 스레드"""
        while not self.stop_event.is_set():
            try:
                # 큐에서 ASR 작업 가져오기 (1초 타임아웃)
                audio_data_np, timestamps, start_idx, snapshot_timestamp_ms = self.asr_queue.get(timeout=1.0)

                # ASR 결과 처리
                asr_results = self._get_asr_results(audio_data_np, timestamps)
                print(f"[ASR Worker] Results: {asr_results}")

                # 결과를 컨텍스트 큐에 추가
                with self.context_audio_deque_lock:
                    for timestamp, result in zip(timestamps, asr_results):
                        start_time = snapshot_timestamp_ms + (timestamp[0] + start_idx) * SAMPLE_TO_MS
                        end_time = snapshot_timestamp_ms + (timestamp[1] + start_idx) * SAMPLE_TO_MS
                        middle_time = int((start_time + end_time) / 2)
                        self.context_audio_deque.append((middle_time, result))

                self.asr_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ASR Worker] Error processing ASR: {e}")
                continue

    def _process_asr_results(
        self, audio_data_np: np.ndarray, timestamps: list[tuple[int, int]], start_idx: int
    ) -> None:
        """ASR 처리를 큐에 추가"""
        snapshot_timestamp_ms = int(time() * 1000)
        self.asr_queue.put((audio_data_np, timestamps, start_idx, snapshot_timestamp_ms))

    def _perform_model_inference_task(self):
        if self.stop_event.is_set():
            print("[Model Inference Task] Stop event set, exiting.")
            return

        audio_data = self.audio_buffer.get_all_data()
        with self.audio_buffer_last_speech_timestamp_idx_lock:
            start_idx = self.audio_buffer_last_speech_timestamp_idx
            print(f"[Model Inference] Start index: {start_idx}, Buffer size: {len(audio_data)}")

        audio_data = audio_data[start_idx:]
        if len(audio_data) % 2 != 0:
            audio_data = audio_data[:-1]
        if not audio_data:
            print("[Model Inference Task] No audio data available, skipping inference.")
            return

        audio_data_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            timestamps = self._get_timestamps(audio_data_np)
            if timestamps:
                last_timestamp = timestamps[-1]
                if last_timestamp[1] + int(self.min_silence_duration_ms / SAMPLE_TO_MS) >= len(audio_data_np):
                    # 다음 seg를 확인해야 하는 경우
                    with self.audio_buffer_last_speech_timestamp_idx_lock:
                        self.audio_buffer_last_speech_timestamp_idx += 2 * last_timestamp[0]
                    if len(timestamps) > 1:
                        timestamps = timestamps[:-1]
                        self._process_asr_results(
                            audio_data_np, timestamps, start_idx
                        )  # start_idx만큼 시간을 계산해야할 것
                else:
                    # 다음 seg를 확인할 필요가 없는 경우
                    with self.audio_buffer_last_speech_timestamp_idx_lock:
                        self.audio_buffer_last_speech_timestamp_idx += 2 * last_timestamp[1]
                    self._process_asr_results(audio_data_np, timestamps, start_idx)
            else:
                with self.audio_buffer_last_speech_timestamp_idx_lock:
                    self.audio_buffer_last_speech_timestamp_idx += len(audio_data_np)
                print("No timestamps found")
        except Exception as e:
            print(f"[Model Inference Task] Error during inference: {e}")

    def _schedule_model_inference_task(self):
        if self.stop_event.is_set():
            print("[Model Inference Task] Stop event set, exiting.")
            return

        self._perform_model_inference_task()

        # 다음 모델 추론을 위한 타이머 재설정 (재귀적으로)
        if self.is_running and not self.stop_event.is_set():
            self.model_inference_timer = threading.Timer(
                MODEL_INFERENCE_INTERVAL_SECONDS, self._schedule_model_inference_task
            )
            self.model_inference_timer.start()
        else:
            print("[Scheduler] Application stopping, model timer not restarted.")

    def _reader_audio_stream(self):
        """stream을 읽어 버퍼에 저장"""
        while self.is_running and not self.stop_event.is_set():
            try:
                if not self.process or not self.process.stdout:
                    print("[Reader] Process or stdout not available.")
                    break
                raw_audio = self.process.stdout.read(FFMPEG_READ_CHUNK_SIZE)
                if not raw_audio:
                    print("FFMPEG stream ended or no more data")
                    break
                self._write_audio_buffer(raw_audio)
            except Exception as e:
                print(f"Error reading audio stream: {e}")
                break
        print("[Reader] Audio stream reader stopped")
        self.stop_event.set()

    def _write_audio_buffer(self, raw_audio: bytes):
        self.audio_buffer.write(raw_audio)
        with self.audio_buffer_last_speech_timestamp_idx_lock:
            updated_last_speech_timestamp_idx = self.audio_buffer_last_speech_timestamp_idx - len(raw_audio)
            self.audio_buffer_last_speech_timestamp_idx = max(
                0, min(updated_last_speech_timestamp_idx, MAX_BUFFER_SIZE)
            )  # 0<=idx<=MAX_BUFFER_SIZE

    def run_async(self):
        if self.m3u8_url == "":
            raise ValueError("m3u8_url is empty")

        self.is_running = True
        try:
            self.process = (
                ffmpeg.input(self.m3u8_url, protocol_whitelist="file,http,https,tcp,tls")
                .output("pipe:", format="s16le", acodec="pcm_s16le", ac=1, ar=TARGET_SAMPLING_RATE)
                .global_args("-fflags", "nobuffer")
                .global_args("-loglevel", "error")
                .run_async(pipe_stdout=True, pipe_stderr=False)
            )
        except Exception as e:
            print(f"Error starting FFMPEG process: {e}")
            self.stop_event.set()
            raise

        # ASR 워커 스레드 시작
        self.asr_thread = threading.Thread(target=self._asr_worker)
        self.asr_thread.daemon = True
        self.asr_thread.start()

        # 1. FFMPEG stdout에서 데이터를 읽어 CircularAudioBuffer에 넣는 스레드
        reader_thread = threading.Thread(target=self._reader_audio_stream)
        reader_thread.daemon = True
        reader_thread.start()

        # 2. 주기적으로 모델 추론을 트리거하는 타이머 시작
        self.model_inference_timer = threading.Timer(
            MODEL_INFERENCE_INTERVAL_SECONDS, self._schedule_model_inference_task
        )
        self.model_inference_timer.start()

        # 메인 스레드는 종료 신호를 기다리면서 대기
        try:
            while not self.stop_event.is_set():
                self.stop_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Stopping application...")
        finally:
            self.stop()

    def stop(self):
        if not self.is_running:
            return

        print("\nStopping AudioStreamProcessor...")
        self.is_running = False
        self.stop_event.set()

        # ASR 큐 비우기
        while not self.asr_queue.empty():
            try:
                self.asr_queue.get_nowait()
                self.asr_queue.task_done()
            except queue.Empty:
                break

        # ASR 스레드 종료 대기
        if self.asr_thread and self.asr_thread.is_alive():
            self.asr_thread.join(timeout=5.0)
            print("ASR worker thread stopped.")

        # Timer 스레드 종료
        if self.model_inference_timer:
            self.model_inference_timer.cancel()
            print("Model inference timer cancelled.")

        # FFMPEG 프로세스 종료
        if self.process:
            print("Terminating FFMPEG process...")
            try:
                # ffmpeg.run_async로 시작된 프로세스는 pipe_stdin=True가 아니면 stdin이 없을 수 있습니다.
                # 필요시 self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
                self.process.terminate()  # 강제 종료
                self.process.wait(timeout=5)  # 프로세스가 종료될 때까지 최대 5초 대기
            except Exception as e:
                print(f"Error terminating FFMPEG process: {e}")
            print("FFMPEG process terminated.")

        print("AudioStreamProcessor stopped cleanly.")

    def get_context_audio(self):
        current_time = int(time() * 1000)
        with self.context_audio_deque_lock:
            while (
                self.context_audio_deque and self.context_audio_deque[0][0] < current_time - AUDIO_CONTEXT_DURATION_MS
            ):
                self.context_audio_deque.popleft()
            results = list(self.context_audio_deque)
        return results
