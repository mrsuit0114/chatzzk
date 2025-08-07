from chzzk_stream_extractor import ChzzkStreamExtractor
from config import Config
from wav_extractor import WavExtractor

config = Config


def test_chzzk_stream_extractor():
    chzzk_stream_extractor = ChzzkStreamExtractor(config.chzzk_stream_extractor)
    while True:
        video_no = input(
            "STEP 1: VOD download", "Enter the video_num (or type 'q' to next step(extract wav from mp4)): "
        )

        if video_no.lower() == "q":
            break

        chzzk_stream_extractor.extract_streams(video_no)


def test_wav_extractor():
    wav_extractor = WavExtractor(config.wav_extractor)
    while True:
        video_no = input("STEP 2: Extract wav from mp4", "Enter the video_num (or type 'q' to next step): ")

        if video_no.lower() == "q":
            break

        wav_extractor.extract_wav_from_mp4(video_no)


def main():
    test_chzzk_stream_extractor()
    test_wav_extractor()


if __name__ == "__main__":
    main()
