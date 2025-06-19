import re

from data_types.context_data import ContextData


class ContextPreprocessor:
    def __init__(self, config: dict, shared_config: dict):
        self.code_to_prompt_cmd = {v: k.upper() for k, v in shared_config["prompt_cmd_to_type_code"].items()}

    def _preprocess_chat_message(self, text: str) -> str:
        # {:...:} 형태 제거
        text = re.sub(r"\{:[^:]*:\}", "", text)

        # 반복되는 자음들 정리
        text = re.sub(r"ㅋ{2,}", "ㅋㅋ", text)
        text = re.sub(r"ㅅ{2,}", "ㅅㅅ", text)
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
