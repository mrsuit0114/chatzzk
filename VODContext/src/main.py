from config import Config
from vod_context_fetcher import VodContextFetcher

config = Config


def main():
    vod_context_fetcher = VodContextFetcher(config)
    while True:
        video_no = input("Enter video_num to make full_context (or type 'q' to exit): ")

        if video_no == "q":
            break

        vod_context_fetcher.run(video_no)


if __name__ == "__main__":
    main()
