import os
import subprocess
import time

from loguru import logger
from tqdm import tqdm

from config import WavExtractorConfig


class WavExtractor:
    def __init__(self, config: WavExtractorConfig):
        self.data_dir = config.DATA_DIR
        self.video_dir = config.VIDEO_DIR
        self.audio_dir = config.AUDIO_DIR
        self.target_sampling_rate = config.TARGET_SAMPLING_RATE

    def extract_wav_from_mp4(self, video_no: int) -> bool:
        """
        Extract a WAV file from an MP4 file with specified configurations.
        Returns True on success, False on failure.
        """
        input_mp4_path = os.path.join(self.data_dir, self.video_dir, f"{video_no}.mp4")
        output_wav_path = os.path.join(self.data_dir, self.audio_dir, f"{video_no}.wav")

        # Check if the input MP4 file exists
        if not os.path.exists(input_mp4_path):
            logger.error(f"❌ Input file not found at {input_mp4_path}")
            return False

        # FFmpeg command and arguments
        command = [
            "ffmpeg",
            "-hide_banner",  # reduce noisy startup output
            "-nostdin",  # do not read from stdin (prevents blocking)
            "-i",
            input_mp4_path,
            "-vn",  # Disable video stream
            "-acodec",
            "pcm_s16le",  # Audio codec (uncompressed WAV)
            "-ar",
            str(self.target_sampling_rate),  # Target sampling rate
            "-ac",
            "1",  # Mono audio
            "-y",  # 파일이 존재하면 자동으로 덮어쓰기
            output_wav_path,
        ]

        # FFmpeg의 stdout/stderr를 캡처하기 위해 Popen 사용
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,  # avoid blocking on stdout
                stderr=subprocess.PIPE,
                universal_newlines=True,  # 텍스트 모드로 스트림 처리
                bufsize=1,  # line-buffered
            )
        except FileNotFoundError:
            logger.error("❌ ffmpeg not found. Please install ffmpeg and ensure it is in PATH.")
            return False

        total_duration = 0.0
        pbar = None

        # FFmpeg의 stderr에서 진행률 정보를 파싱
        try:
            last_update_time = 0.0
            for line in process.stderr:
                # 총 영상 길이를 먼저 파싱
                if "Duration:" in line:
                    try:
                        parts = line.split(",")[0].split(" ")[-1].strip()
                        h, m, s = parts.split(":")
                        total_duration = float(h) * 3600 + float(m) * 60 + float(s)
                        if total_duration > 0:
                            pbar = tqdm(total=total_duration, unit="s", desc="Extracting Audio")
                    except Exception:
                        # Duration 파싱 실패 시 진행바 없이 계속
                        total_duration = 0.0

                # 현재 진행 시간(time)을 파싱하여 진행률 바 업데이트
                if "time=" in line and pbar:
                    now = time.monotonic()
                    if now - last_update_time >= 0.25:
                        last_update_time = now
                        try:
                            time_str = line.split("time=")[-1].split(" ")[0]
                            h, m, s = time_str.split(":")
                            current_time = float(h) * 3600 + float(m) * 60 + float(s)
                            increment = max(0.0, current_time - pbar.n)
                            if increment:
                                pbar.update(increment)  # 업데이트된 만큼만 증가
                        except Exception:
                            pass

            # 프로세스가 완료될 때까지 대기
            process.wait()
            if pbar:
                pbar.close()

            if process.returncode != 0:
                stdout_output, stderr_output = process.communicate()
                logger.error(f"❌ ffmpeg failed with return code {process.returncode}")
                if stdout_output:
                    logger.debug(f"ffmpeg stdout: {stdout_output.strip()}")
                if stderr_output:
                    logger.error(f"ffmpeg stderr: {stderr_output.strip()}")
                return False
            else:
                logger.info(f"✅ Successfully extracted: {output_wav_path}")
                return True

        except Exception as e:
            if pbar:
                pbar.close()
            logger.error(f"❌ Unexpected error during WAV extraction: {e}")
            return False
