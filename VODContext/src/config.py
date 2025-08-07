import os


class SharedConfig:
    DATA_DIR = "data"
    VIDEO_DIR = "videos"
    AUDIO_DIR = "audios"
    CHAT_CONTEXT_DIR = "chat_contexts"
    ASR_CONTEXT_DIR = "asr_contexts"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"


def create_directories(config: SharedConfig):
    """
    Checks for the existence of required directories and creates them if they don't exist.
    """
    # Create the base data directory
    os.makedirs(config.DATA_DIR, exist_ok=True)

    # Create subdirectories under the data directory
    sub_directories = [
        config.VIDEO_DIR,
        config.AUDIO_DIR,
        config.CHAT_CONTEXT_DIR,
        config.ASR_CONTEXT_DIR,
    ]

    for sub_dir in sub_directories:
        path = os.path.join(config.DATA_DIR, sub_dir)
        os.makedirs(path, exist_ok=True)
        print(f"Directory created or already exists: {path}")


create_directories(SharedConfig)


class ChzzkStreamExtractorConfig:
    VOD_URL = "https://apis.naver.com/neonplayer/vodplay/v2/playback/{video_id}?key={in_key}"
    VOD_INFO = "https://api.chzzk.naver.com/service/v2/videos/{video_no}"
    DATA_DIR = SharedConfig.DATA_DIR
    VIDEO_DIR = SharedConfig.VIDEO_DIR
    USER_AGENT = SharedConfig.USER_AGENT


class WavExtractorConfig:
    DATA_DIR = SharedConfig.DATA_DIR
    VIDEO_DIR = SharedConfig.VIDEO_DIR
    AUDIO_DIR = SharedConfig.AUDIO_DIR
    TARGET_SAMPLING_RATE = 16000


class Config:
    shared = SharedConfig()
    chzzk_stream_extractor = ChzzkStreamExtractorConfig()
    wav_extractor = WavExtractorConfig()
