import re
from typing import Optional

from data_types.context_data import ContextData


class ContextPreprocessor:
    def __init__(self, config: dict, shared_config: dict):
        self.code_to_prompt_cmd = {v: k.upper() for k, v in shared_config["prompt_cmd_to_type_code"].items()}
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

    def preprocess_chat_context(self, chats: list[ContextData]) -> list[ContextData]:
        preprocessed_chat_context = []
        for chat in chats:
            text = self._preprocess_chat_message(chat.content)
            if text == "":
                continue
            preprocessed_chat_context.append(
                ContextData(
                    chat.timestamp_ms,
                    chat.content,
                    chat.type_code,
                    f"[{self.code_to_prompt_cmd[chat.type_code]}] {text}\n",
                )
            )
        return preprocessed_chat_context

    def preprocess_audio_context(self, audio_context: list[ContextData]) -> list[ContextData]:
        preprocessed_audio_context = []
        for asr in audio_context:
            text = self._preprocess_asr(asr.content)
            if text is None:
                continue
            preprocessed_audio_context.append(
                ContextData(
                    asr.timestamp_ms, text, asr.type_code, f"[{self.code_to_prompt_cmd[asr.type_code]}] {text}\n"
                )
            )
        return preprocessed_audio_context

    def _preprocess_asr(self, asr: str) -> Optional[str]:
        if asr == "" or any(not_expected_asr in asr for not_expected_asr in self.NOT_EXPECTED_ASR):
            return None

        return asr
