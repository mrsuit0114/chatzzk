import re


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


def preprocess(chats: list[dict]) -> list[dict]:  # (ms, text, type)
    preprocessed_chats = []
    for chat in chats:
        text = preprocess_chat_message(chat["message"])
        if text == "":
            continue
        timestamp_ms = chat["timestamp_ms"]
        type = chat["type"]
        preprocessed_chats.append({"timestamp_ms": timestamp_ms, "text": text, "type": type})
    return preprocessed_chats
