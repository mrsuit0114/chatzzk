import os


class SharedConfig:
    PROMPT_CMD_TO_TYPE_CODE: dict[str, int] = {"chat": 100, "donation": 1000, "asr": 10000}


class ChatConfig:
    MAX_CHAT_HISTORY_COUNT: int = 10000
    CHZZK_CHAT_CODE: dict[str, int] = {
        "ping": 0,
        "pong": 10000,
        "connect": 100,
        "send_chat": 3101,
        "request_recent_chat": 5101,
        "chat": 93101,
        "donation": 93102,
    }


class AudioConfig:
    TARGET_SAMPLING_RATE: int = 16000
    MODEL_INFERENCE_INTERVAL_S: int = 2
    MIN_SILENCE_DURATION_MS: int = 500
    MAX_SPEECH_DURATION_S: int = 30
    BYTES_PER_SAMPLE: int = 2
    OFFSET_MS: int = 1500
    MODEL_SIZE: str = "large-v3"
    M3U8_PROXY_URL: str = "https://chzzk-api-proxy.hibiya.workers.dev/m3u8-redirect/{channel_id}"
    NOT_EXPECTED_ASR_LIST: list[str] = [
        "MBC",
        "스토리였습니다",
        "세계였습니다",
        "시청해주셔서",
        "고맙습니다",
        "감사합니다",
        "날씨였습니다",
        "기상캐스터",
        "수고하셨습니다",
    ]


class ContextConfig:
    CONTEXT_UPDATE_INTERVAL_S: int = 1
    CONTEXT_SAVE_INTERVAL_S: int = 5
    CONTEXT_SAVE_PATH: str = "./data/history/context_history.jsonl"
    ASR_CONTEXT_DURATION_MS: int = 130000
    CHAT_CONTEXT_DURATION_MS: int = 120000
    HISTORY_TOPIC_PREFIX = "history-updates:"
    PROMPT_TOPIC_PREFIX = "prompt-updates:"


class ContextFetcherConfig:
    shared = SharedConfig()
    chat = ChatConfig()
    audio = AudioConfig()
    context = ContextConfig()


class RedisConfig:
    REDIS_URL = os.environ.get("REDIS_URL", "")
