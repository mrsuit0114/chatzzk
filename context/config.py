class SharedConfig:
    PROMPT_CMD_TO_TYPE_CODE = {"chat": 100, "donation": 1000, "asr": 10000}


class ChatConfig:
    MAX_CHAT_HISTORY_COUNT = 10000
    CHZZK_CHAT_CODE = {
        "ping": 0,
        "pong": 10000,
        "connect": 100,
        "send_chat": 3101,
        "request_recent_chat": 5101,
        "chat": 93101,
        "donation": 93102,
    }
