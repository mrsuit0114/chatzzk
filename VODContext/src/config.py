import os


class SharedConfig:
    DATA_DIR = os.getenv("VOD_DATA_DIR", "data")
    VIDEO_DIR = os.getenv("VOD_VIDEO_DIR", "videos")
    AUDIO_DIR = os.getenv("VOD_AUDIO_DIR", "audios")
    CHAT_CONTEXT_DIR = os.getenv("VOD_CHAT_CONTEXT_DIR", "chat_contexts")
    VAD_DIR = os.getenv("VOD_VAD_DIR", "vads")
    ASR_CONTEXT_DIR = os.getenv("VOD_ASR_CONTEXT_DIR", "asr_contexts")
    FULL_CONTEXT_DIR = os.getenv("VOD_FULL_CONTEXT_DIR", "full_contexts")
    USER_AGENT = os.getenv(
        "VOD_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    )
    PROMPT_CMD_TO_TYPE_CODE: dict[str, int] = {"chat": 100, "donation": 1000, "asr": 10000}


def create_directories(config: SharedConfig):
    """
    Checks for the existence of required directories and creates them if they don't exist.
    """
    try:
        # Create the base data directory
        os.makedirs(config.DATA_DIR, exist_ok=True)

        # Create subdirectories under the data directory
        sub_directories = [
            config.VIDEO_DIR,
            config.AUDIO_DIR,
            config.CHAT_CONTEXT_DIR,
            config.ASR_CONTEXT_DIR,
            config.VAD_DIR,
            config.FULL_CONTEXT_DIR,
        ]

        for sub_dir in sub_directories:
            path = os.path.join(config.DATA_DIR, sub_dir)
            os.makedirs(path, exist_ok=True)
            print(f"✅ Directory created or already exists: {path}")

    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        raise


# Initialize directories when module is imported
create_directories(SharedConfig)


class ChzzkStreamExtractorConfig:
    VOD_URL = "https://apis.naver.com/neonplayer/vodplay/v2/playback/{video_id}?key={in_key}"
    VOD_INFO = "https://api.chzzk.naver.com/service/v2/videos/{video_no}"
    DATA_DIR = SharedConfig.DATA_DIR
    VIDEO_DIR = SharedConfig.VIDEO_DIR
    USER_AGENT = SharedConfig.USER_AGENT
    COOKIES_FILE = os.getenv("VOD_COOKIES_FILE", "cookies.json")
    MAX_RETRIES = int(os.getenv("VOD_MAX_RETRIES", "3"))
    TIMEOUT = int(os.getenv("VOD_TIMEOUT", "30"))


class WavExtractorConfig:
    DATA_DIR = SharedConfig.DATA_DIR
    VIDEO_DIR = SharedConfig.VIDEO_DIR
    AUDIO_DIR = SharedConfig.AUDIO_DIR
    TARGET_SAMPLING_RATE = int(os.getenv("VOD_TARGET_SAMPLING_RATE", "16000"))


class ChzzkChatCrawlerConfig:
    CHAT_URL = "https://api.chzzk.naver.com/service/v1/videos/{video_no}/chats"
    USER_AGENT = SharedConfig.USER_AGENT
    DATA_DIR = SharedConfig.DATA_DIR
    CHAT_CONTEXT_DIR = SharedConfig.CHAT_CONTEXT_DIR
    PROMPT_CMD_TO_TYPE_CODE = SharedConfig.PROMPT_CMD_TO_TYPE_CODE
    MESSAGE_TYPE_CODE_TO_PROMPT_CMD = {1: "chat", 10: "donation"}
    MAX_RETRIES = int(os.getenv("VOD_CHAT_MAX_RETRIES", "3"))
    BASE_SLEEP_TIME = float(os.getenv("VOD_CHAT_BASE_SLEEP_TIME", "0.5"))


class AudioProcessorConfig:
    DATA_DIR = SharedConfig.DATA_DIR
    AUDIO_DIR = SharedConfig.AUDIO_DIR
    VAD_DIR = SharedConfig.VAD_DIR
    ASR_CONTEXT_DIR = SharedConfig.ASR_CONTEXT_DIR
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
    MODEL_SIZE = os.getenv("VOD_ASR_MODEL_SIZE", "large-v3")
    MIN_SILENCE_DURATION_MS = int(os.getenv("VOD_MIN_SILENCE_DURATION_MS", "500"))
    MAX_SPEECH_DURATION_S = int(os.getenv("VOD_MAX_SPEECH_DURATION_S", "30"))
    ASR_TYPE_CODE = 10000
    ASR_PAY_AMOUNT = 0
    WHISPERX_MODEL_DIR = os.getenv("VOD_WHISPERX_MODEL_DIR", "/app/whisperx_models")
    COMPUTE_TYPE = os.getenv("VOD_COMPUTE_TYPE", "float16")
    BATCH_SIZE = int(os.getenv("VOD_BATCH_SIZE", "4"))


class ContextMergeManagerConfig:
    DATA_DIR = SharedConfig.DATA_DIR
    ASR_CONTEXT_DIR = SharedConfig.ASR_CONTEXT_DIR
    CHAT_CONTEXT_DIR = SharedConfig.CHAT_CONTEXT_DIR
    FULL_CONTEXT_DIR = SharedConfig.FULL_CONTEXT_DIR
    ASR_CONTEXT_DEFAULT_OFFSET_MS = int(os.getenv("VOD_ASR_OFFSET_MS", "500"))


class Config:
    def __init__(self):
        self.shared = SharedConfig()
        self.chzzk_stream_extractor = ChzzkStreamExtractorConfig()
        self.wav_extractor = WavExtractorConfig()
        self.chzzk_chat_crawler = ChzzkChatCrawlerConfig()
        self.audio_processor = AudioProcessorConfig()
        self.context_merge_manager = ContextMergeManagerConfig()
