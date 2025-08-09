from audio_processor import AudioProcessor
from chzzk_chat_crawler import ChzzkChatCrawler
from chzzk_stream_extractor import ChzzkStreamExtractor
from config import Config
from wav_extractor import WavExtractor

config = Config


def test_chzzk_stream_extractor():
    chzzk_stream_extractor = ChzzkStreamExtractor(config.chzzk_stream_extractor)
    while True:
        video_no = input(
            "STEP 1: VOD download, Enter the video_num (or type 'q' to next step(to extract wav from mp4)): "
        )

        if video_no.lower() == "q":
            break

        chzzk_stream_extractor.extract_streams(video_no)


def test_wav_extractor():
    wav_extractor = WavExtractor(config.wav_extractor)
    while True:
        video_no = input(
            "STEP 2: Extract wav from mp4, Enter the video_num (or type 'q' to next step(crawling chat)): "
        )

        if video_no.lower() == "q":
            break

        wav_extractor.extract_wav_from_mp4(video_no)


def test_chzzk_chat_crawler():
    chzzk_chat_crawler = ChzzkChatCrawler(config.chzzk_chat_crawler)
    while True:
        video_no = input("STEP 3: Crawl chat, Enter the video_num (or type 'q' to next step(vad processing)): ")

        if video_no.lower() == "q":
            break

        chzzk_chat_crawler.crawl_chat(video_no)


def test_audio_processor():
    audio_processor = AudioProcessor(config.audio_processor)
    while True:
        video_no = input("STEP 4: Vad processing, Enter the video_num (or type 'q' to next step): ")

        if video_no.lower() == "q":
            break

        audio_processor.process_audio(video_no, True)


def main():
    # test_chzzk_stream_extractor()
    # test_wav_extractor()
    # test_chzzk_chat_crawler()
    test_audio_processor()


if __name__ == "__main__":
    main()
