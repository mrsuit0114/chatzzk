# video_no를 받아서 full_context jsonl을 반환하는 역할을 담당
# 채팅내역 크롤링은 영상과는 독립적으로 수행이 가능하기 때문에 병렬로 수행
# 채팅을 그렇게 빨리 시작할 필요는 없기 때문에 가장 우선은 영상이 다운 받아지는지

import concurrent
from concurrent.futures import ThreadPoolExecutor

from audio_processor import AudioProcessor
from chzzk_chat_crawler import ChzzkChatCrawler
from chzzk_stream_extractor import ChzzkStreamExtractor
from config import Config
from context_merge_manager import ContextMergeManager
from wav_extractor import WavExtractor


class VodContextFetcher:
    def __init__(self, config: Config):
        self.chzzk_stream_extractor = ChzzkStreamExtractor(config.chzzk_stream_extractor)
        self.chzzk_chat_crawler = ChzzkChatCrawler(config.chzzk_chat_crawler)
        self.wav_extractor = WavExtractor(config.wav_extractor)
        self.audio_processor = AudioProcessor(config.audio_processor)
        self.context_merge_manager = ContextMergeManager(config.context_merge_manager)

    def run(self, video_no: int, vad_save=False):
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 1단계: 스트림 추출
            # Future 객체를 반환하여 작업이 완료될 때까지 기다릴 수 있습니다.
            future_step1 = executor.submit(self.chzzk_stream_extractor.extract_streams, video_no)

            # 1단계가 완료될 때까지 기다림
            future_step1.result()
            print("-" * 20)

            # 1단계 완료 후 2, 3, 4단계 병렬 실행
            # 4단계는 3단계의 Future 객체를 사용해 의존성을 관리
            future_step2 = executor.submit(self.chzzk_chat_crawler.crawl_chat, video_no)
            future_step3 = executor.submit(self.wav_extractor.extract_wav_from_mp4, video_no)

            # 3단계가 완료될 때까지 기다린 후 4단계 실행
            future_step4 = executor.submit(lambda: self._run_step4_after_step3(future_step3, video_no, vad_save))

            # 2, 3, 4단계가 모두 완료될 때까지 기다림
            concurrent.futures.wait([future_step2, future_step3, future_step4])
            print("-" * 20)

            # 2, 3, 4단계 완료 후 5단계 실행
            future_step5 = executor.submit(self.context_merge_manager.merge_context, video_no)

            # 5단계 완료를 기다림
            future_step5.result()

    def _run_step4_after_step3(self, future_step3, video_no, vad_save):
        # 3단계의 결과를 기다림
        future_step3.result()
        # 4단계 작업 실행
        self.audio_processor.process_audio(video_no, vad_save)
