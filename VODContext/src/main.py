from chzzk_stream_extractor import ChzzkStreamExtractor
from config import Config

config = Config


def main():
    chzzk_stream_extractor = ChzzkStreamExtractor(config)
    while True:
        video_no = input("Enter the video_num (or type 'q' to quit): ")

        if video_no.lower() == "q":
            break

        chzzk_stream_extractor.extract_streams(video_no)


if __name__ == "__main__":
    main()
