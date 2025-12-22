# 나중에는 값을 yaml 파일로 옮기고 읽어오기만 해야할 듯 -> 빌드 컨텍스트에 포함되어 골치아픔
from enum import Enum


class PlatformCode(str, Enum):
    CHZZK = "chzzk"
    YOUTUBE = "youtube"
    SOOP = "sooplive"


class VODPipelineStatus(str, Enum):
    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태


class VODProcessingStep(str, Enum):
    CRAWL_CHATS = "crawl_chats"
    DOWNLOAD_AUDIO = "download_audio"
    PERFORM_VAD = "perform_vad"
    PERFORM_ASR = "perform_asr"
    GENERATE_SUMMARY = "generate_summary"
    GENERATE_META_SUMMARY = "generate_meta_summary"


class VODPipelineStepStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


# -------------- db init value -------------------------
class DBDefault:
    IS_ACTIVE = "true"
    IS_EXPOSED = "true"

    VOD_PIPELINE_STATUS = VODPipelineStatus.PENDING.value

    class Len:
        ID = 256
        NAME = 256
        URL = 512


class AudioDataConstant:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_DTYPE_STR = "float32"
    ACODEC = "pcm_s32le"
    MAX_SPEECH_DURATION_S = 30


class MLModelPaths:
    MODEL_BASE: str = "models"
    WHISPERX: str = f"{MODEL_BASE}/whisperx"


class EntryType(str, Enum):
    CHAT = "CHAT"
    DONATION = "DONATION"
    ASR = "ASR"
    SUMMARY = "SUMMARY"
    META_SUMMARY = "META_SUMMARY"


ASR_HALLUCINATION_KEYWORDS = [
    "뉴스",
    "고맙습니다",
    "감사합니다",
    "였습니다",
    "MBC",
]


class LLMTask(str, Enum):
    SUMMARIZE = "summarize"
    META_SUMMARIZE = "meta_summarize"


class LLMPromptPaths:
    BY_TASK = {
        LLMTask.SUMMARIZE: "stream/segment-analyzer",
        LLMTask.META_SUMMARIZE: "stream/context-integrator",
    }


class StreamAtmosphere(str, Enum):
    SADNESS = "슬픔"
    NEUTRAL = "중립"
    HILARIOUS = "폭소"
    ANGER = "분노"
    ADMIRATION = "감탄"
    ANTICIPATION = "기대"


class ScoreCategory(str, Enum):
    EXPRESIVENESS = "expresiveness"
    COHERENCE = "coherence"
    SIGNIFICANCE = "significance"


class StreamContextWindowSize:
    # entries의 timestamp에 대한 window size, 단위는 ms
    # CHUNK: int = 30 * 1000  채팅과 도네이션 이벤트를 기준으로 탐색할 때 길지도 짧지도 않아야 함
    SUMMARY: int = 300 * 1000
    META_SUMMARY: int = 3600 * 1000


class StoragePaths:
    AUDIO = "{vod_id}/audio.wav"
    CHAT = "{vod_id}/chat_entries.jsonl"
    VAD_TIMESTAMPS = "{vod_id}/vad_timestamps.jsonl"
    ASR = "{vod_id}/asr_entries.jsonl"
    SUMMARY_RAW = "{vod_id}/summary_raw_entries.jsonl"
    SUMMARY = "{vod_id}/summary_entries.jsonl"
    META_SUMMARY = "{vod_id}/meta_summary_entries.jsonl"

    TMP_VIDEO = "{vod_id}/tmp/video.mp4"
    TMP_DIR = "{vod_id}/tmp"

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
    def get_summary_raw_key(cls, vod_id: str | int) -> str:
        return cls.SUMMARY_RAW.format(vod_id=vod_id)

    @classmethod
    def get_summary_key(cls, vod_id: str | int) -> str:
        return cls.SUMMARY.format(vod_id=vod_id)

    @classmethod
    def get_meta_summary_key(cls, vod_id: str | int) -> str:
        return cls.META_SUMMARY.format(vod_id=vod_id)

    @classmethod
    def get_tmp_dir(cls, vod_id: str | int) -> str:
        return cls.TMP_DIR.format(vod_id=vod_id)
