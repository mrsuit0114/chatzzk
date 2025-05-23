# m3u8을 주기적으로 확인하여 최신 오디오 segment를 가져옴
# 리샘플링(48khz -> 16khz) 수행하여 tensor로 반환

import datetime
import threading
import time
from queue import Queue

import ffmpeg
import numpy as np

from audio.asr import ASR
from audio.circular_audio_buffer import CircularAudioBuffer
from audio.vad import VAD

ORIGINAL_SAMPLING_RATE = 48000
TARGET_SAMPLING_RATE = 16000
BUFFER_DURATION = 30  # 30 seconds buffer
BYTES_PER_SAMPLE = 2
MAX_BUFFER_SIZE = TARGET_SAMPLING_RATE * BYTES_PER_SAMPLE * BUFFER_DURATION

# 2초마다 모델 추론을 수행하도록 설정
MODEL_INFERENCE_INTERVAL_SECONDS = 2
FFMPEG_READ_CHUNK_SIZE = 4096  # ffmpeg stdout에서 한 번에 읽어올 청크 크기 (바이트)


class AudioStreamProcessor:
    """요청한 시점에 context에 포함될 오디오 데이터를 반환해야함
    [(ms, content), ... ]
    """

    def __init__(self):
        self.m3u8_url: str = ""
        self.process = None
        self.is_running = False
        self.stop_event = threading.Event()

        self.vad = VAD()
        self.asr = ASR()

        self.audio_buffer = CircularAudioBuffer(MAX_BUFFER_SIZE)
        self.context_audio_queue: Queue[tuple[int, str]] = Queue()

        self.model_inference_timer = None

    def set_m3u8_url(self, m3u8_url: str):
        self.m3u8_url = m3u8_url

    def _merge_timestamps(self, timestamps: list[tuple[int, int]], threshold_ms: int = 800):
        threshold_samples = threshold_ms * TARGET_SAMPLING_RATE // 1000
        merged_timestamps = []
        current_start: int | None = None
        current_end: int | None = None

        for start, end in timestamps:
            if current_start is None:
                current_start = start
                current_end = end
            elif start - current_end <= threshold_samples:  # type: ignore
                current_end = end
            else:
                merged_timestamps.append((current_start, current_end))
                current_start = start
                current_end = end

        if current_start is not None:
            merged_timestamps.append((current_start, current_end))

        return merged_timestamps

    def _get_merged_timestamps(self, audio_data: np.ndarray):
        timestamps = self.vad(audio_data)
        merged_timestamps = self._merge_timestamps(timestamps)
        return merged_timestamps

    def _get_asr_results(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
        asr_results = self.asr(audio_data, timestamps)
        return asr_results

    def _perform_model_inference_task(self):
        if self.stop_event.is_set():
            print("[Model Inference Task] Stop event set, exiting.")
            return
        print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] [Model Inference] Attempting inference...")

        audio_data = self.audio_buffer.get_all_data()
        if not audio_data:
            print("[Model Inference Task] No audio data available, skipping inference.")
            return

        audio_data_np = np.frombuffer(audio_data, dtype=np.int16)
        try:
            timestamps = self._get_merged_timestamps(audio_data_np)
            if timestamps:
                asr_results = self._get_asr_results(audio_data_np, timestamps)
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] [Model Inference] Results: {asr_results}")
            else:
                print("No timestamps found")
        except Exception as e:
            print(f"[Model Inference Task] Error during inference: {e}")

    def _schedule_model_inference_task(self):
        if self.stop_event.is_set():
            print("[Model Inference Task] Stop event set, exiting.")
            return

        self._perform_model_inference_task()  # 실제 모델 추론 로직 호출

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
                self.audio_buffer.write(raw_audio)
            except Exception as e:
                print(f"Error reading audio stream: {e}")
                break
        print("[Reader] Audio stream reader stopped")
        self.stop_event.set()

    def run_async(self):
        if self.m3u8_url == "":
            raise ValueError("m3u8_url is empty")

        self.is_running = True
        try:
            self.process = (
                ffmpeg.input(self.m3u8_url, protocol_whitelist="file,http,https,tcp,tls")
                .output("pipe:", format="s16le", acodec="pcm_s16le", ac=1, ar=TARGET_SAMPLING_RATE)
                .global_args("-fflags", "nobuffer")
                .run_async(pipe_stdout=True, pipe_stderr=False)
            )
        except Exception as e:
            print(f"Error starting FFMPEG process: {e}")
            self.stop_event.set()
            raise

        # 1. FFMPEG stdout에서 데이터를 읽어 CircularAudioBuffer에 넣는 스레드
        reader_thread = threading.Thread(target=self._reader_audio_stream)
        reader_thread.daemon = True
        reader_thread.start()

        # 2. 주기적으로 모델 추론을 트리거하는 타이머 시작
        # 첫 실행도 2초 후에 시작되도록 설정
        self.model_inference_timer = threading.Timer(
            MODEL_INFERENCE_INTERVAL_SECONDS, self._schedule_model_inference_task
        )
        self.model_inference_timer.start()

        # 메인 스레드는 종료 신호를 기다리면서 대기
        try:
            while self.is_running and not self.stop_event.is_set():
                time.sleep(0.1)  # 짧게 대기하며 종료 신호 확인
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Stopping application...")
        finally:
            self.stop()  # 애플리케이션 종료 처리

    def stop(self):
        if not self.is_running:
            return

        print("\nStopping AudioStreamProcessor...")
        self.is_running = False
        self.stop_event.set()  # 모든 스레드에 종료 신호 보냄

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
