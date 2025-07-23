import threading
from collections import deque
from heapq import merge
from time import time

from loguru import logger

from audio.audio_stream_processor import AudioStreamProcessor
from chat.chat_stream_processor import ChatStreamProcessor
from config import ContextFetcherConfig
from data_types.context_data import ContextData
from redis_client import RedisClient


class ContextFetcher:
    STOP_TIMEOUT_S = 5

    def __init__(self, channel_id: str, config: ContextFetcherConfig, redis_client: RedisClient = None):
        self.channel_id = channel_id
        # self.redis_client = redis_client
        # self.history_topic = config.
        # self.prompt_topic = config.

        self.prompt_cmd_to_type_code = config.shared.PROMPT_CMD_TO_TYPE_CODE
        self.type_code_to_prompt_cmd = {v: k.upper() for k, v in self.prompt_cmd_to_type_code.items()}
        self.asr_context_duration_ms = config.context.ASR_CONTEXT_DURATION_MS
        self.chat_context_duration_ms = config.context.CHAT_CONTEXT_DURATION_MS
        self.update_interval_s = config.context.CONTEXT_UPDATE_INTERVAL_S
        self.history_publish_interval_s = config.context.CONTEXT_SAVE_INTERVAL_S

        self.audio_stream_processor = AudioStreamProcessor(channel_id, config.audio, config.shared)
        self.chat_stream_processor = ChatStreamProcessor(channel_id, config.chat, config.shared)

        self.context_history_batch: deque[ContextData] = deque(maxlen=1000)
        self.context_history_lock = threading.Lock()
        self.prompt_buffer: deque[ContextData] = deque(maxlen=1000)
        self.prompt_buffer_lock = threading.Lock()

        # 스레드 관리
        self.stop_event = threading.Event()
        self.threads = [
            threading.Thread(target=self.audio_stream_processor.run, name="AudioProcessorThread"),
            threading.Thread(target=self.chat_stream_processor.run, name="ChatProcessorThread"),
            threading.Thread(target=self._update_loop, name="UpdateLoop"),
        ]
        for thread in self.threads:
            thread.daemon = True

    def _update_loop(self):
        """컨텍스트를 주기적으로 업데이트하는 메인 루프"""
        while not self.stop_event.wait(self.update_interval_s):
            cur_timestamp_ms = int(time() * 1000)
            new_context = self._get_new_context()

            if new_context:
                self._add_to_history_batch(new_context)
                self._update_prompt_buffer(new_context, cur_timestamp_ms)
        logger.info("Update loop finished.")

    def _get_new_context(self) -> list[ContextData]:
        """오디오 및 채팅 프로세서에서 새로운 컨텍스트를 가져와 병합합니다."""
        chat_contexts = self.chat_stream_processor.get_new_chats()
        asr_contexts = self.audio_stream_processor.get_new_asr_results()

        return list(merge(chat_contexts, asr_contexts, key=lambda x: x.timestamp_ms))

    def _add_to_history_batch(self, new_context: list[ContextData]):
        """DB 저장을 위한 기록 버퍼에 새 컨텍스트를 추가합니다."""
        with self.context_history_lock:
            self.context_history_batch.extend(new_context)

    def _is_valid_for_prompt_duration(self, context: ContextData, cur_timestamp_ms: int) -> bool:
        type_code = context.type_code
        if type_code in (self.prompt_cmd_to_type_code["chat"], self.prompt_cmd_to_type_code["donation"]):
            return context.timestamp_ms > cur_timestamp_ms - self.chat_context_duration_ms
        elif type_code == self.prompt_cmd_to_type_code["asr"]:
            return context.timestamp_ms > cur_timestamp_ms - self.asr_context_duration_ms
        return False

    def _update_prompt_buffer(self, new_context: list[ContextData], cur_timestamp_ms: int):
        """LLM 프롬프트 버퍼를 최신 상태로 업데이트합니다."""
        with self.prompt_buffer_lock:
            while self.prompt_buffer and not self._is_valid_for_prompt_duration(
                self.prompt_buffer[0], cur_timestamp_ms
            ):
                self.prompt_buffer.popleft()

            valid_new_context_gen = (c for c in new_context if c.prompt_str)
            merged_context = merge(self.prompt_buffer, valid_new_context_gen, key=lambda x: x.timestamp_ms)
            self.prompt_buffer = deque(merged_context)

    def _get_prompt_cmd(self, context: ContextData):
        return self.type_code_to_prompt_cmd[context.type_code]

    def get_context_prompt(self) -> str:
        with self.prompt_buffer_lock:
            return "".join(
                f"{context.timestamp_ms}: [{self._get_prompt_cmd(context)}] {context.prompt_str}"
                for context in self.prompt_buffer
            )

    def run(self):
        """ContextFetcher의 모든 스레드를 시작합니다."""
        logger.info("Starting ContextFetcher...")
        self.stop_event.clear()
        for thread in self.threads:
            thread.start()
        logger.info("ContextFetcher started.")

    def stop(self):
        """ContextFetcher의 모든 스레드와 프로세스를 안전하게 종료합니다."""
        logger.info("Stopping ContextFetcher...")
        self.stop_event.set()

        self.audio_stream_processor.stop()
        self.chat_stream_processor.stop()

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=self.STOP_TIMEOUT_S)
                if thread.is_alive():
                    logger.warning(f"Thread {thread.name} did not terminate gracefully.")

        logger.info("ContextFetcher stopped.")
