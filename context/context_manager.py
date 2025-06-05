import threading
from time import time

from audio.audio_stream_processor import AudioStreamProcessor
from chat.chat_stream_processor import ChatStreamProcessor
from context.context_preprocess import ContextPreprocessor


class ContextManager:
    def __init__(self, channel_id: str, config: dict):
        self.config = config
        self.audio_stream_processor = AudioStreamProcessor(channel_id, config["audio"])
        self.chat_stream_processor = ChatStreamProcessor(channel_id, config["chat"])
        self.audio_stream_processor_thread = None
        self.chat_stream_processor_thread = None
        self.context_preprocessor = ContextPreprocessor(config["context"])

    def run(self):
        self.audio_stream_processor_thread = threading.Thread(target=self.audio_stream_processor.run)
        self.chat_stream_processor_thread = threading.Thread(target=self.chat_stream_processor.run)
        self.audio_stream_processor_thread.start()
        self.chat_stream_processor_thread.start()

    def get_context(self):
        timestamp_ms = int(time() * 1000)
        chat_context = self.chat_stream_processor.get_latest_chats_since(timestamp_ms)
        audio_context = self.audio_stream_processor.get_latest_asr_since(timestamp_ms)
        preprocessed_chat_context = self.context_preprocessor.preprocess_chat_context(chat_context)
        preprocessed_audio_context = self.context_preprocessor.preprocess_audio_context(audio_context)

        merged_context = []
        i, j = 0, 0
        while i < len(preprocessed_chat_context) and j < len(preprocessed_audio_context):
            if preprocessed_chat_context[i].timestamp_ms < preprocessed_audio_context[j].timestamp_ms:
                merged_context.append(preprocessed_chat_context[i])
                i += 1
            else:
                merged_context.append(preprocessed_audio_context[j])
                j += 1
        while i < len(preprocessed_chat_context):
            merged_context.append(preprocessed_chat_context[i])
            i += 1
        while j < len(preprocessed_audio_context):
            merged_context.append(preprocessed_audio_context[j])
            j += 1

        return merged_context

    def stop(self):
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
