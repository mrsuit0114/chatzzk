class SharedConfig:
    DATA_DIR = "data/"
    VIDEO_DIR = "videos/"
    AUDIO_DIR = "audios/"
    CHAT_CONTEXT_DIR = "chat_contexts/"
    ASR_CONTEXT_DIR = "asr_contexts/"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"


# 각 폴더 유무 확인 및 생성까지


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
