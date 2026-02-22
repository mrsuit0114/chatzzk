# 나중에는 값을 yaml 파일로 옮기고 읽어오기만 해야할 듯 -> 빌드 컨텍스트에 포함되어 골치아픔
# StrEnum이 db 컬럼의 타입인 경우 postgresql enum에 따라 key를 기준으로 타입이 정의되는 것으로 보임 -> 대문자 키로 정의됨
# 그 외에 컬럼의 타입으로 정의되지는 않았지만 jsonb에서 strenum이 사용되는 경우(pipline log, channel metadata 등)가 있으나
# jsonb는 비정형 데이터도 포함되기 때문에 소문자로 통일할 것
from enum import IntEnum, StrEnum


class PlatformCode(StrEnum):
    CHZZK = "CHZZK"
    YOUTUBE = "YOUTUBE"
    SOOP = "SOOP"


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    USER = "USER"


class VODPipelineStatus(StrEnum):
    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태


class VODProcessingStep(StrEnum):
    CRAWL_CHATS = "crawl_chats"
    DOWNLOAD_AUDIO = "download_audio"
    PERFORM_VAD = "perform_vad"
    PERFORM_ASR = "perform_asr"
    GENERATE_SEGMENT_SUMMARY = "generate_segment_summary"
    GENERATE_CHAPTER_SUMMARY = "generate_chapter_summary"
    GENERATE_ANALYSIS = "generate_analysis"


class VODPipelineStepStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class AudioDataConstant:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_DTYPE_STR = "float32"
    ACODEC = "pcm_s32le"
    MAX_SPEECH_DURATION_S = 30
    MIN_SILENCE_DURATION_MS = 500
    CHUNK_DURATION_S = 600.0  # 스트리밍 과정에서 한 번에 로드할 오디오 청크의 길이


class MLModelPaths:
    MODEL_BASE: str = "models"
    WHISPERX: str = f"{MODEL_BASE}/whisperx"


class EntryType(StrEnum):
    CHAT = "CHAT"
    DONATION = "DONATION"
    ASR = "ASR"
    SEGMENT_SUMMARY = "SEGMENT_SUMMARY"
    CHAPTER_SUMMARY = "CHAPTER_SUMMARY"


class EntryTypeCode(IntEnum):
    CHAT = 1
    DONATION = 2
    ASR = 3
    SEGMENT_SUMMARY = 10
    CHAPTER_SUMMARY = 11

    @classmethod
    def from_entry_type(cls, entry_type: EntryType) -> int:
        return cls[entry_type]


ASR_HALLUCINATION_KEYWORDS = [
    "뉴스 스토리였습니다",
    "고맙습니다",
    "감사합니다",
    "세계였습니다",
    "MBC 뉴스",
    "다음 영상에서 만나요",
    "다음 주에 만나요",
    "자막 제공",
    "날씨였습니다",
    "영상편집 및 자료조사",
    "영상편집 박진주",
]


class LLMTask(StrEnum):
    SEGMENT_SUMMARIZE = "segment_summarize"
    CHAPTER_SUMMARIZE = "chapter_summarize"


# LLMTask와 구분하면 다대일, 버전관리가 용이함
LLM_PROMPT_PATHS = {
    LLMTask.SEGMENT_SUMMARIZE: "segment-summarizer",
    LLMTask.CHAPTER_SUMMARIZE: "chapter-summarizer",
}


class StreamAtmosphere(StrEnum):
    NEUTRAL = "중립"
    HILARIOUS = "폭소"
    SADNESS = "슬픔"
    ANGER = "분노"
    BOOING = "야유"
    ADMIRATION = "감탄"
    ANTICIPATION = "기대"
    ENCOURAGEMENT = "격려"


class StreamWindowConstant:
    # ms
    CLIP_SIZE: int = 30 * 1000
    SEGMENT_SIZE: int = 300 * 1000
    CHAPTER_SIZE: int = 3600 * 1000
    STREAM_LOG_PADDING_SIZE: int = 5 * 60 * 1000


class StoragePaths:
    AUDIO = "{vod_id}/audio.wav"
    CHAT = "{vod_id}/chat_entries.jsonl"
    VAD_TIMESTAMPS = "{vod_id}/vad_timestamps.jsonl"
    ASR = "{vod_id}/asr_entries.jsonl"
    SEGMENT_SUMMARY = "{vod_id}/segment_summary_entries.jsonl"
    CHAPTER_SUMMARY = "{vod_id}/chapter_summary_entries.jsonl"

    TMP_VIDEO = "{vod_id}/tmp/video.mp4"
    TMP_DIR = "{vod_id}/tmp"

    WEB_DIR = "{vod_id}/web"
    ANALYSIS = "{vod_id}/web/analysis.json"
    STREAM_LOGS = "{vod_id}/web/stream_logs_{index}.json"

    @classmethod
    def get_tmp_video_key(cls, vod_id: str | int) -> str:
        return cls.TMP_VIDEO.format(vod_id=vod_id)

    @classmethod
    def get_audio_key(cls, vod_id: str | int) -> str:
        return cls.AUDIO.format(vod_id=vod_id)

    @classmethod
    def get_chat_key(cls, vod_id: str | int) -> str:
        return cls.CHAT.format(vod_id=vod_id)

    @classmethod
    def get_vad_timestamps_key(cls, vod_id: str | int) -> str:
        return cls.VAD_TIMESTAMPS.format(vod_id=vod_id)

    @classmethod
    def get_asr_key(cls, vod_id: str | int) -> str:
        return cls.ASR.format(vod_id=vod_id)

    @classmethod
    def get_segment_summary_key(cls, vod_id: str | int) -> str:
        return cls.SEGMENT_SUMMARY.format(vod_id=vod_id)

    @classmethod
    def get_analysis_key(cls, vod_id: str | int) -> str:
        return cls.ANALYSIS.format(vod_id=vod_id)

    @classmethod
    def get_stream_logs_key(cls, vod_id: str | int, index: int) -> str:
        return cls.STREAM_LOGS.format(vod_id=vod_id, index=index)

    @classmethod
    def get_chapter_summary_key(cls, vod_id: str | int) -> str:
        return cls.CHAPTER_SUMMARY.format(vod_id=vod_id)

    @classmethod
    def get_tmp_dir(cls, vod_id: str | int) -> str:
        return cls.TMP_DIR.format(vod_id=vod_id)

    @classmethod
    def get_web_dir(cls, vod_id: str | int) -> str:
        return cls.WEB_DIR.format(vod_id=vod_id)


class BucketPaths:
    VOD_DIR = "vods/{vod_id}"

    @classmethod
    def get_vod_prefix(cls, vod_id: str | int) -> str:
        return cls.VOD_DIR.format(vod_id=vod_id)
