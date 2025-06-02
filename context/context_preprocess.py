import re
from typing import Optional

from data_types.context_data import ContextData


def preprocess_chat_message(text: str) -> str:
    # {:...:} 형태 제거
    text = re.sub(r"\{:[^:]*:\}", "", text)

    # 'ㅋ' 하나 이상 → 'ㅋㅋ'
    if "ㅋ" in text:
        text = re.sub(r"ㅋ+", "ㅋㅋ", text)

    # 'ㅅ' 하나 이상 → 'ㅅㅅ'
    if "ㅅ" in text:
        text = re.sub(r"ㅅ+", "ㅅㅅ", text)

    return text.strip()


def preprocess_chat_context(chats: list[ContextData]) -> list[ContextData]:  # (ms, text, type)
    preprocessed_chats = []
    for chat in chats:
        text = preprocess_chat_message(chat.content)
        if text == "":
            continue
        preprocessed_chats.append(ContextData(chat.timestamp_ms, text, chat.type))
    return preprocessed_chats


def preprocess_audio_context(audio_context: list[ContextData]) -> list[ContextData]:
    preprocessed_audio_context = []
    for asr in audio_context:
        text = preprocess_asr(asr.content)
        if text is None:
            continue
        preprocessed_audio_context.append(ContextData(asr.timestamp_ms, text, asr.type))
    return preprocessed_audio_context


def preprocess_asr(asr: str) -> Optional[str]:
    if "MBC" in asr:  # 발언하지 않았음에도 'MBC 기자 누구입니다.'가 나와 제외함
        return None
    if asr == "":
        return None
    return asr
