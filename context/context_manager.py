import json
import threading
from collections import deque
from heapq import merge
from time import time

from context.audio.audio_stream_processor import AudioStreamProcessor
from context.chat.chat_stream_processor import ChatStreamProcessor
from context.context_preprocess import ContextPreprocessor
from data_types.context_data import ContextData


class ContextManager:
    def __init__(self, channel_id: str, config: dict):
        self.prompt_cmd_to_type_code = config["shared_config"]["prompt_cmd_to_type_code"]
        self.type_code_to_prompt_cmd = {v: k.upper() for k, v in self.prompt_cmd_to_type_code.items()}
        self.asr_context_duration_ms = config["context"]["asr_context_duration_ms"]
        self.chat_context_duration_ms = config["context"]["chat_context_duration_ms"]
        self.context_update_interval_s = config["context"]["context_update_interval_s"]
        self.context_save_interval_s = config["context"]["context_save_interval_s"]
        self.context_save_path = config["context"]["context_save_path"]

        self.audio_stream_processor = AudioStreamProcessor(channel_id, config["audio"], config["shared_config"])
        self.chat_stream_processor = ChatStreamProcessor(channel_id, config["chat"], config["shared_config"])
        self.context_preprocessor = ContextPreprocessor(config["context"], config["shared_config"])

        self.audio_stream_processor_thread = None
        self.chat_stream_processor_thread = None

        # 스케줄러 관련 변수들
        self.update_timer = None
        self.save_timer = None
        self.running = False

        self.context_history: list[ContextData] = []
        self.context_history_lock = threading.Lock()
        self.context_prompt_buffer: deque[ContextData] = deque()
        self.context_prompt_lock = threading.Lock()

    def run(self):
        self.audio_stream_processor_thread = threading.Thread(target=self.audio_stream_processor.run)
        self.chat_stream_processor_thread = threading.Thread(target=self.chat_stream_processor.run)
        self.audio_stream_processor_thread.start()
        self.chat_stream_processor_thread.start()

        # 주기적 작업 시작
        self.running = True
        self._schedule_update_context()
        self._schedule_save_context_history()

    def _schedule_update_context(self):
        """1초마다 update_context를 호출하는 스케줄러"""
        if self.running:
            cur_timestamp_ms = int(time() * 1000)
            self._update_context(cur_timestamp_ms)
            self.update_timer = threading.Timer(self.context_update_interval_s, self._schedule_update_context)
            self.update_timer.start()

    def _schedule_save_context_history(self):
        """5초마다 _save_context_history를 호출하는 스케줄러"""
        if self.running:
            self._flush_context_history_to_file()
            self.save_timer = threading.Timer(self.context_save_interval_s, self._schedule_save_context_history)
            self.save_timer.start()

    def _update_context(self, cur_timestamp_ms: int):  # 주기적으로 호출 필요
        new_context = self._get_new_context()
        threading.Thread(target=self._update_context_history, args=(new_context,)).start()
        threading.Thread(target=self._update_context_prompt, args=(new_context, cur_timestamp_ms)).start()

    def _get_new_context(self) -> list[ContextData]:
        chat_contexts = self.chat_stream_processor.get_new_chats()
        processed_chat_contexts = self.context_preprocessor.preprocess_chat_context(chat_contexts)
        asr_contexts = self.audio_stream_processor.get_new_asr_results()

        return self._get_combined_context(processed_chat_contexts, asr_contexts)

    def _get_combined_context(
        self, chat_contexts: list[ContextData], asr_contexts: list[ContextData]
    ) -> list[ContextData]:
        return list(merge(chat_contexts, asr_contexts, key=lambda x: x.timestamp_ms))

    def _update_context_history(self, new_context: list[ContextData]):  # 주기적으로 저장하여 비워줘야함
        with self.context_history_lock:
            self.context_history.extend(new_context)

    def _flush_context_history_to_file(self):
        with self.context_history_lock:
            new_context_history = self.context_history.copy()
            self.context_history.clear()
        with open(self.context_save_path, "a", encoding="utf-8") as f:
            for context in new_context_history:
                f.write(json.dumps(context._asdict(), ensure_ascii=False) + "\n")

    def _is_valid_context_prompt(self, context: ContextData, cur_timestamp_ms: int) -> bool:
        if (
            context.type_code == self.prompt_cmd_to_type_code["chat"]
            or context.type_code == self.prompt_cmd_to_type_code["donation"]
        ):
            return context.timestamp_ms > cur_timestamp_ms - self.chat_context_duration_ms
        elif context.type_code == self.prompt_cmd_to_type_code["asr"]:
            return context.timestamp_ms > cur_timestamp_ms - self.asr_context_duration_ms
        return False

    def _update_context_prompt(self, new_context: list[ContextData], cur_timestamp_ms: int):
        updated_context_prompt_buffer = []
        with self.context_prompt_lock:
            while self.context_prompt_buffer:
                cur_context = self.context_prompt_buffer.popleft()
                if self._is_valid_context_prompt(cur_context, cur_timestamp_ms):
                    updated_context_prompt_buffer.append(cur_context)

            updated_context_prompt_buffer.extend(new_context)
            self.context_prompt_buffer = deque(updated_context_prompt_buffer)

    def get_context_prompt(self) -> str:  # 언제 호출해도 프롬프트에 적합한 context_prompt를 반환
        with self.context_prompt_lock:
            cur_context_prompt_buffer = self.context_prompt_buffer.copy()
        context_prompt = "".join(context.prompt_str for context in cur_context_prompt_buffer)
        return context_prompt

    def stop(self):
        # 스케줄러 중지
        self.running = False
        if self.update_timer:
            self.update_timer.cancel()
        if self.save_timer:
            self.save_timer.cancel()

        # 마지막 저장 실행
        self._flush_context_history_to_file()

        self.audio_stream_processor.stop()
        self.chat_stream_processor.stop()

        if self.audio_stream_processor_thread and self.audio_stream_processor_thread.is_alive():
            self.audio_stream_processor_thread.join(timeout=5.0)
            if self.audio_stream_processor_thread.is_alive():
                print("Warning: Audio stream processor thread did not terminate gracefully")

        if self.chat_stream_processor_thread and self.chat_stream_processor_thread.is_alive():
            self.chat_stream_processor_thread.join(timeout=5.0)
            if self.chat_stream_processor_thread.is_alive():
                print("Warning: Chat stream processor thread did not terminate gracefully")
