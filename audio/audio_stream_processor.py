# m3u8을 주기적으로 확인하여 최신 오디오 segment를 가져옴
# 리샘플링(48khz -> 16khz) 수행하여 tensor로 반환

import datetime
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
        self.context_audio_deque: deque[tuple[int, str]] = deque()
        self.context_audio_lock = threading.Lock()
        self.last_speech_timestamp_ms = 0

        self.model_inference_timer = None

    def set_m3u8_url(self, m3u8_url: str):
        self.m3u8_url = m3u8_url

    def _get_timestamps(self, audio_data: np.ndarray):
        timestamps = self.vad(audio_data)
        return timestamps

    def _get_asr_results(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
        asr_results = self.asr(audio_data, timestamps)
        return asr_results

    def _get_after_last_speech_timestamp(self, timestamps: list[tuple[int, int]], snapshot_timestamp_ms: int):
        # timestamps에서 가장 마지막 음성 이후의 경우만 필터링, 마지막 음성이 이어지는 경우 한개인 경우는 빈 리스트 반환, 여러개인 경우 [:-1] 반환하고 시간을 갱신
        # 중복된 구간에 대해 ASR을 시도하지 않기 위해, 현재 시간을 받아 샘플의 시간을 계산해서 마지막 처리된 음성보다 시간이 큰 경우만 처리
        after_last_speech_timestamps = [
            timestamp
            for timestamp in timestamps
            if snapshot_timestamp_ms + timestamp[0] * SAMPLE_TO_MS > self.last_speech_timestamp_ms
        ]
        # 추출된 timestamps가 있는 경우
        if after_last_speech_timestamps:
            # 마지막 데이터의 끝 timestamp의 ms와 self.min_silence_duration_ms을 더했을 때 self.max_speech_duration_ms보다 크면 음성이 이어질 수 있으므로 다음 seg를 봐야함
            if (
                after_last_speech_timestamps[-1][1] * SAMPLE_TO_MS + self.min_silence_duration_ms
                >= self.max_speech_duration_ms
            ):
                # 여러개인 경우 마지막 데이터 제외하고 반환하고 시간 갱신
                if len(after_last_speech_timestamps) > 1:
                    self.last_speech_timestamp_ms = snapshot_timestamp_ms + int(
                        after_last_speech_timestamps[-2][1] * SAMPLE_TO_MS
                    )
                    return after_last_speech_timestamps[:-1]
            else:
                self.last_speech_timestamp_ms = snapshot_timestamp_ms + int(
                    after_last_speech_timestamps[-1][1] * SAMPLE_TO_MS
                )
                return after_last_speech_timestamps

        return []

    def _perform_model_inference_task(self):
        if self.stop_event.is_set():
            print("[Model Inference Task] Stop event set, exiting.")
            return
        print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] [Model Inference] Attempting inference...")

        audio_data = self.audio_buffer.get_all_data()
        if not audio_data:
            print("[Model Inference Task] No audio data available, skipping inference.")
            return

        audio_data_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            timestamps = self._get_timestamps(audio_data_np)
            if timestamps:
                snapshot_timestamp_ms = int(time() * 1000)
                after_last_speech_timestamps = self._get_after_last_speech_timestamp(timestamps, snapshot_timestamp_ms)
                asr_results = self._get_asr_results(audio_data_np, after_last_speech_timestamps)
                with self.context_audio_lock:
                    for after_last_speech_timestamp, result in zip(after_last_speech_timestamps, asr_results):
                        start_time = snapshot_timestamp_ms + after_last_speech_timestamp[0] * SAMPLE_TO_MS
                        end_time = snapshot_timestamp_ms + after_last_speech_timestamp[1] * SAMPLE_TO_MS
                        middle_time = int((start_time + end_time) / 2)
                        self.context_audio_deque.append((middle_time, result))
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
                .run_async(pipe_stdout=True, pipe_stderr=False)  # stderr로 받으려면 다른 곳에서 처리를 해줘야함
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
            while not self.stop_event.is_set():
                self.stop_event.wait(timeout=1.0)  # 1초마다 체크
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

    def get_context_audio(self):
        with self.context_audio_lock:
            while self.context_audio_deque and self.context_audio_deque[0][0] < time() - 30:
                self.context_audio_deque.popleft()
            results = list(self.context_audio_deque)
        return results
