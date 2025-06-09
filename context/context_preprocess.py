import re
from typing import Optional

from data_types.context_data import ContextData


class ContextPreprocessor:
    def __init__(self, config: dict):
        self.config = config
        self.NOT_EXPECTED_ASR = set(config["asr_not_expected_list"])

    def _preprocess_chat_message(self, text: str) -> str:
        # {:...:} 형태 제거
        text = re.sub(r"\{:[^:]*:\}", "", text)

        if re.search(r"ㅋ{2,}", text):
            text = re.sub(r"ㅋ{2,}", "ㅋㅋ", text)

        if re.search(r"ㅅ{2,}", text):
            text = re.sub(r"ㅅ{2,}", "ㅅㅅ", text)

        if re.search(r"ㅊ{2,}", text):
            text = re.sub(r"ㅊ{2,}", "ㅊㅊ", text)

        return text.strip()

    def preprocess_chat_context(self, chats: list[ContextData]) -> list[ContextData]:  # (ms, text, type)
        preprocessed_chats = []
        for chat in chats:
            text = self._preprocess_chat_message(chat.content)
            if text == "":
                continue
            preprocessed_chats.append(ContextData(chat.timestamp_ms, text, chat.type))
        return preprocessed_chats

    def preprocess_audio_context(self, audio_context: list[ContextData]) -> list[ContextData]:
        preprocessed_audio_context = []
        for asr in audio_context:
            text = self._preprocess_asr(asr.content)
            if text is None:
                continue
            preprocessed_audio_context.append(ContextData(asr.timestamp_ms, text, asr.type))
        return preprocessed_audio_context

    def _preprocess_asr(self, asr: str) -> Optional[str]:
        if any(
            not_expected_asr in asr for not_expected_asr in self.NOT_EXPECTED_ASR
        ):  # 발언하지 않았음에도 'MBC 기자 누구입니다.'가 나와 제외함
            return None
        if asr == "":
            return None

        return asr
