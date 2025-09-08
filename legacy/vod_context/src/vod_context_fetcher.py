import os
from concurrent.futures import ThreadPoolExecutor

from common.buckets import BucketNames
from common.clients.storage import MinioStorageClient
from loguru import logger

from clients.chzzk_chat_crawler import ChzzkChatCrawler
from clients.chzzk_stream_extractor import ChzzkStreamExtractor
from config import Config
from core.data_manager import DataManager
from processing.audio_processor import AudioProcessor
from processing.context_merge_manager import ContextMergeManager
from processing.wav_extractor import WavExtractor


class VodContextFetcher:
    def __init__(self, config: Config):
        self.data_manager = DataManager(config)
        self.chzzk_stream_extractor = ChzzkStreamExtractor(config, self.data_manager)
        self.chzzk_chat_crawler = ChzzkChatCrawler(config)
        self.wav_extractor = WavExtractor(config, self.data_manager)
        self.audio_processor = AudioProcessor(config)
        self.context_merge_manager = ContextMergeManager()
        self.storage_client = MinioStorageClient(config.storage_config)

    def run(self, video_no: int, vad_save: bool = False) -> bool:
        """Run the complete VOD context fetching pipeline with error handling."""
        try:
            logger.info(f"🚀 Starting VOD context fetching for video {video_no}")

            video_mp4_path = self.data_manager.get_video_path(video_no)
            chat_jsonl_path = self.data_manager.get_chat_context_path(video_no)
            wav_path = self.data_manager.get_audio_path(video_no)
            vad_path = self.data_manager.get_vad_path(video_no)
            asr_jsonl_path = self.data_manager.get_asr_context_path(video_no)
            full_context_jsonl_path = self.data_manager.get_full_context_path(video_no)

            # Step 1: Stream extraction (must be done first)
            if not os.path.exists(video_mp4_path):
                logger.info("📹 Step 1: Extracting video streams...")
                if not self.chzzk_stream_extractor.extract_streams(video_no):
                    logger.error(f"❌ Step 1 failed for video {video_no}")
                    return False
                logger.info("✅ Step 1 completed: Video streams extracted")
            else:
                logger.info(f"⏭️ Skipping Step 1: video already exists at {video_mp4_path}")

            logger.info("-" * 50)

            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit chat and audio pipelines to run in parallel
                future_chat = executor.submit(self._get_chat_contexts, video_no, chat_jsonl_path)
                future_asr = executor.submit(
                    self._get_asr_contexts, video_no, wav_path, asr_jsonl_path, vad_path, vad_save
                )

                chat_contexts = future_chat.result()
                asr_contexts = future_asr.result()

            if chat_contexts is None or asr_contexts is None:
                logger.error("❌ Failed to get contexts from chat or audio pipeline.")
                return False

            logger.info("-" * 50)

            # Step 5: Context merging
            if os.path.exists(full_context_jsonl_path):
                logger.info(f"⏭️ Skipping Context Merge: file exists at {full_context_jsonl_path}")
                merged_context_saved = True
            else:
                logger.info("🔗 Step 5: Merging contexts...")
                merged_context = self.context_merge_manager.merge_context(chat_contexts, asr_contexts)
                merged_context_saved = self.data_manager.save_jsonl(merged_context, full_context_jsonl_path)
                if merged_context_saved:
                    logger.info("✅ Step 5 completed: Contexts merged successfully")
                else:
                    logger.error("❌ Step 5 failed: Could not save merged context")

            # Step 6: Upload to MinIO
            if merged_context_saved:
                logger.info("📤 Step 6: Uploading full context to storage...")
                try:
                    with open(full_context_jsonl_path, "rb") as f:
                        self.storage_client.upload(f"{video_no}.jsonl", f.read(), BucketNames.VOD_CONTEXTS)
                    logger.info("✅ Step 6 completed: Upload successful")
                except Exception as e:
                    logger.error(f"❌ Step 6 failed: Could not upload to storage. {e}")
                    # Not returning false, just logging the error.

            logger.info(f"🎉 VOD context fetching completed successfully for video {video_no}")
            return True

        except Exception as e:
            logger.error(f"❌ Unexpected error during VOD context fetching for {video_no}: {e}")
            return False

    def _get_chat_contexts(self, video_no: int, path: str):
        if os.path.exists(path):
            logger.info(f"⏭️ Loading chat contexts from {path}")
            return self.data_manager.load_context_data_from_jsonl(path)
        else:
            logger.info(f"💬 Starting chat crawling for video {video_no}")
            contexts = self.chzzk_chat_crawler.crawl_chat(video_no)
            self.data_manager.save_jsonl(contexts, path)
            logger.info(f"✅ Chat crawling completed and saved to {path}")
            return contexts

    def _get_asr_contexts(self, video_no: int, wav_path: str, asr_path: str, vad_path: str, vad_save: bool):
        if os.path.exists(asr_path):
            logger.info(f"⏭️ Loading ASR contexts from {asr_path}")
            return self.data_manager.load_context_data_from_jsonl(asr_path)

        if not os.path.exists(wav_path):
            logger.info(f"🎵 Starting WAV extraction for video {video_no}")
            if not self.wav_extractor.extract_wav_from_mp4(video_no):
                raise RuntimeError("Failed to extract WAV file.")
            logger.info("✅ WAV extraction completed.")
        else:
            logger.info(f"⏭️ Skipping WAV Extraction: file exists at {wav_path}")

        vad_timestamps, asr_contexts = self.audio_processor.process_audio(wav_path)

        self.data_manager.save_jsonl(asr_contexts, asr_path)
        logger.info(f"✅ ASR contexts saved to {asr_path}")
        if vad_save:
            self.data_manager.save_jsonl(vad_timestamps, vad_path)
            logger.info(f"✅ VAD timestamps saved to {vad_path}")

        return asr_contexts
