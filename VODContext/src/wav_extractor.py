import os
import subprocess

from tqdm import tqdm

from config import WavExtractorConfig


class WavExtractor:
    def __init__(self, config: WavExtractorConfig):
        self.data_dir = config.DATA_DIR
        self.video_dir = config.VIDEO_DIR
        self.audio_dir = config.AUDIO_DIR
        self.target_sampling_rate = config.TARGET_SAMPLING_RATE

    def extract_wav_from_mp4(self, video_no: int):
        """
        Extracts a WAV file from an MP4 file with specified configurations.
        """
        input_mp4_path = os.path.join(self.data_dir, self.video_dir, f"{video_no}.mp4")
        output_wav_path = os.path.join(self.data_dir, self.audio_dir, f"{video_no}.wav")

        # Check if the input MP4 file exists
        if not os.path.exists(input_mp4_path):
            print(f"Error: Input file not found at {input_mp4_path}")
            return

        # FFmpeg command and arguments
        command = [
            "ffmpeg",
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
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,  # 텍스트 모드로 스트림 처리
        )

        total_duration = 0.0
        pbar = None

        # FFmpeg의 stderr에서 진행률 정보를 파싱
        try:
            for line in process.stderr:
                # 총 영상 길이를 먼저 파싱
                if "Duration:" in line:
                    parts = line.split(",")[0].split(" ")[-1].strip()
                    h, m, s = map(float, parts.split(":"))
                    total_duration = h * 3600 + m * 60 + s
                    pbar = tqdm(total=total_duration, unit="s", desc="Extracting Audio")

                # 현재 진행 시간(time)을 파싱하여 진행률 바 업데이트
                if "time=" in line and pbar:
                    time_str = line.split("time=")[-1].split(" ")[0]
                    h, m, s = map(float, time_str.split(":"))
                    current_time = h * 3600 + m * 60 + s
                    pbar.update(current_time - pbar.n)  # 업데이트된 만큼만 증가

            # 프로세스가 완료될 때까지 대기
            process.wait()
            if pbar:
                pbar.close()

            if process.returncode != 0:
                stdout_output, stderr_output = process.communicate()
                print(f"Error during ffmpeg execution: Return code {process.returncode}")
                print("FFmpeg stdout:", stdout_output)
                print("FFmpeg stderr:", stderr_output)
            else:
                print(f"Successfully extracted: {output_wav_path}")

        except Exception as e:
            if pbar:
                pbar.close()
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":

    class TmpConfig:
        """A simple configuration class for WavExtractor."""

        DATA_DIR = "data/"
        VIDEO_DIR = "videos/"
        AUDIO_DIR = "audios/"
        TARGET_SAMPLING_RATE = 16000

    config = TmpConfig()
    wav_extractor = WavExtractor(config)
    while True:
        video_no = input("input video_no or 'q' to exit")
        wav_extractor.extract_wav_from_mp4(video_no)
