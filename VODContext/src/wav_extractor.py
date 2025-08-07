import os
import subprocess

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
            output_wav_path,
        ]

        try:
            # Run the ffmpeg command
            subprocess.run(command, check=True, text=True, capture_output=True)
            print(f"Successfully extracted: {output_wav_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error during ffmpeg execution: {e}")
            print("FFmpeg stdout:", e.stdout)
            print("FFmpeg stderr:", e.stderr)
        except FileNotFoundError:
            print("Error: FFmpeg command not found. Please ensure FFmpeg is installed and in your system's PATH.")


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
