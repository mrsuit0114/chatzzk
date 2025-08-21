import os

from common.clients.storage import StorageConfig
from loguru import logger


class Config:
    class ASR:
        MODEL_SIZE = os.getenv("VOD_ASR_MODEL_SIZE", "large-v3")
        MODEL_DIR = os.getenv("VOD_ASR_MODEL_DIR", "/app/whisperx_models")
        COMPUTE_TYPE = os.getenv("VOD_ASR_COMPUTE_TYPE", "float16")
        BATCH_SIZE = int(os.getenv("VOD_ASR_BATCH_SIZE", "4"))
        LANGUAGE = os.getenv("VOD_ASR_LANGUAGE", "ko")
        CONTEXT_DEFAULT_OFFSET_MS = int(os.getenv("VOD_ASR_OFFSET_MS", "500"))

        NOT_EXPECTED_ASR_LIST = [
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

    class VAD:
        MIN_SILENCE_DURATION_MS = int(os.getenv("VOD_VAD_MIN_SILENCE_DURATION_MS", "500"))
        MAX_SPEECH_DURATION_S = int(os.getenv("VOD_VAD_MAX_SPEECH_DURATION_S", "30"))

    class DataDir:
        DATA_DIR = os.getenv("VOD_DATA_DIR", "data")
        VIDEO_DIR = os.path.join(DATA_DIR, os.getenv("VOD_VIDEO_DIR", "videos"))
        AUDIO_DIR = os.path.join(DATA_DIR, os.getenv("VOD_AUDIO_DIR", "audios"))
        CHAT_CONTEXT_DIR = os.path.join(DATA_DIR, os.getenv("VOD_CHAT_CONTEXT_DIR", "chat_contexts"))
        VAD_DIR = os.path.join(DATA_DIR, os.getenv("VOD_VAD_DIR", "vads"))
        ASR_CONTEXT_DIR = os.path.join(DATA_DIR, os.getenv("VOD_ASR_CONTEXT_DIR", "asr_contexts"))
        FULL_CONTEXT_DIR = os.path.join(DATA_DIR, os.getenv("VOD_FULL_CONTEXT_DIR", "full_contexts"))

        ALL_DIRS = [DATA_DIR, VIDEO_DIR, AUDIO_DIR, CHAT_CONTEXT_DIR, VAD_DIR, ASR_CONTEXT_DIR, FULL_CONTEXT_DIR]

    class Network:
        USER_AGENT = os.getenv(
            "VOD_USER_AGENT",
            "",
        )
        HTTP_MAX_RETRIES = int(os.getenv("VOD_HTTP_MAX_RETRIES", "3"))
        HTTP_TIMEOUT = int(os.getenv("VOD_HTTP_TIMEOUT", "30"))
        HTTP_BASE_SLEEP_TIME = float(os.getenv("VOD_HTTP_BASE_SLEEP_TIME", "0.5"))

    class ChzzkStream:
        VOD_URL = os.getenv("VOD_URL", "")
        VOD_INFO = os.getenv("VOD_INFO", "")
        COOKIES_FILE = os.getenv("VOD_COOKIES_FILE", "cookies.json")

    class ChzzkChat:
        CHAT_URL = os.getenv("VOD_CHAT_URL", "")

    class Audio:
        TARGET_SAMPLING_RATE = int(os.getenv("VOD_TARGET_SAMPLING_RATE", "16000"))

    class Minio:
        ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
        ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
        SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "adminadmin")
        SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

    def __init__(self):
        try:
            for directory in self.DataDir.ALL_DIRS:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✅ Directory ready: {directory}")
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            raise

        self.storage_config = StorageConfig(
            endpoint=self.Minio.ENDPOINT,
            access_key=self.Minio.ACCESS_KEY,
            secret_key=self.Minio.SECRET_KEY,
            secure=self.Minio.SECURE,
        )
