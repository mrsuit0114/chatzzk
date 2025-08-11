# video_no를 받아서 full_context jsonl을 반환하는 역할을 담당
# 채팅내역 크롤링은 영상과는 독립적으로 수행이 가능하기 때문에 병렬로 수행
# 채팅을 그렇게 빨리 시작할 필요는 없기 때문에 가장 우선은 영상이 다운 받아지는지

import os
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

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

    def run(self, video_no: int, vad_save: bool = False) -> bool:
        """Run the complete VOD context fetching pipeline with error handling.

        Skip each step when its expected output already exists.
        """
        try:
            logger.info(f"🚀 Starting VOD context fetching for video {video_no}")

            # Build output paths for skip checks
            video_mp4_path = os.path.join(
                self.chzzk_stream_extractor.data_dir,
                self.chzzk_stream_extractor.video_dir,
                f"{video_no}.mp4",
            )
            chat_jsonl_path = os.path.join(
                self.chzzk_chat_crawler.data_dir,
                self.chzzk_chat_crawler.chat_context_dir,
                f"{video_no}.jsonl",
            )
            wav_path = os.path.join(
                self.wav_extractor.data_dir,
                self.wav_extractor.audio_dir,
                f"{video_no}.wav",
            )
            asr_jsonl_path = os.path.join(
                self.audio_processor.data_dir,
                self.audio_processor.asr_context_dir,
                f"{video_no}.jsonl",
            )
            full_context_jsonl_path = os.path.join(
                self.context_merge_manager.data_dir,
                self.context_merge_manager.full_context_dir,
                f"{video_no}.jsonl",
            )

            with ThreadPoolExecutor(max_workers=4) as executor:
                # Step 1: Stream extraction (must complete first)
                if os.path.exists(video_mp4_path):
                    logger.info(f"⏭️ Skipping Step 1: video already exists at {video_mp4_path}")
                    step1_success = True
                else:
                    logger.info("📹 Step 1: Extracting video streams...")
                    future_step1 = executor.submit(self.chzzk_stream_extractor.extract_streams, video_no)
                    try:
                        step1_success = future_step1.result()
                        if not step1_success:
                            logger.error(f"❌ Step 1 failed for video {video_no}")
                            return False
                        logger.info("✅ Step 1 completed: Video streams extracted")
                    except Exception as e:
                        logger.error(f"❌ Step 1 failed with exception: {e}")
                        return False

                logger.info("-" * 50)

                # Steps 2, 3, 4: Parallel execution
                logger.info("🔄 Steps 2-4: Running in parallel...")

                # Step 2: Chat crawling
                if os.path.exists(chat_jsonl_path):
                    logger.info(f"⏭️ Skipping Chat Crawling: file exists at {chat_jsonl_path}")
                    future_step2 = executor.submit(lambda: True)
                else:
                    future_step2 = executor.submit(self._run_chat_crawling, video_no)

                # Step 3: WAV extraction
                if os.path.exists(wav_path):
                    logger.info(f"⏭️ Skipping WAV Extraction: file exists at {wav_path}")
                    future_step3 = executor.submit(lambda: True)
                else:
                    future_step3 = executor.submit(self._run_wav_extraction, video_no)

                # Step 4: Audio processing (depends on step 3)
                if os.path.exists(asr_jsonl_path):
                    logger.info(f"⏭️ Skipping Audio Processing (ASR): file exists at {asr_jsonl_path}")
                    # still wait for step3 if it was running to keep pipeline order sane
                    future_step4 = executor.submit(lambda: (future_step3.result(), True)[1])
                else:
                    future_step4 = executor.submit(self._run_audio_processing, future_step3, video_no, vad_save)

                # Wait for all parallel steps to complete
                step_results = {}
                for future, step_name in [
                    (future_step2, "Chat Crawling"),
                    (future_step3, "WAV Extraction"),
                    (future_step4, "Audio Processing"),
                ]:
                    try:
                        result = future.result()
                        step_results[step_name] = result
                        status = "✅" if result else "❌"
                        logger.info(f"{status} {step_name} completed")
                    except Exception as e:
                        logger.error(f"❌ {step_name} failed with exception: {e}")
                        step_results[step_name] = False

                # Check if all steps succeeded
                if not all(step_results.values()):
                    failed_steps = [step for step, success in step_results.items() if not success]
                    logger.error(f"❌ Failed steps: {', '.join(failed_steps)}")
                    return False

                logger.info("-" * 50)

                # Step 5: Context merging
                if os.path.exists(full_context_jsonl_path):
                    logger.info(f"⏭️ Skipping Context Merge: file exists at {full_context_jsonl_path}")
                else:
                    logger.info("🔗 Step 5: Merging contexts...")
                    try:
                        future_step5 = executor.submit(self.context_merge_manager.merge_context, video_no)
                        step5_success = future_step5.result()
                        if step5_success:
                            logger.info("✅ Step 5 completed: Contexts merged successfully")
                        else:
                            logger.error("❌ Step 5 failed: Context merging failed")
                            return False
                    except Exception as e:
                        logger.error(f"❌ Step 5 failed with exception: {e}")
                        return False

            logger.info(f"🎉 VOD context fetching completed successfully for video {video_no}")
            return True

        except Exception as e:
            logger.error(f"❌ Unexpected error during VOD context fetching for {video_no}: {e}")
            return False

    def _run_chat_crawling(self, video_no: int) -> bool:
        """Run chat crawling with error handling."""
        try:
            logger.info(f"💬 Starting chat crawling for video {video_no}")
            return self.chzzk_chat_crawler.crawl_chat(video_no)
        except Exception as e:
            logger.error(f"❌ Chat crawling failed for video {video_no}: {e}")
            return False

    def _run_wav_extraction(self, video_no: int) -> bool:
        """Run WAV extraction with error handling."""
        try:
            logger.info(f"🎵 Starting WAV extraction for video {video_no}")
            return self.wav_extractor.extract_wav_from_mp4(video_no)
        except Exception as e:
            logger.error(f"❌ WAV extraction failed for video {video_no}: {e}")
            return False

    def _run_audio_processing(self, future_step3, video_no: int, vad_save: bool) -> bool:
        """Run audio processing after WAV extraction completes."""
        try:
            # Wait for step 3 to complete
            wav_ok = future_step3.result()
            if not wav_ok:
                logger.error(f"❌ Skipping audio processing because WAV extraction failed for video {video_no}")
                return False
            logger.info(f"🎤 Starting audio processing for video {video_no}")
            return self.audio_processor.process_audio(video_no, vad_save)
        except Exception as e:
            logger.error(f"❌ Audio processing failed for video {video_no}: {e}")
            return False
