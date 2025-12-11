# 나중에는 값을 yaml 파일로 옮기고 읽어오기만 해야할 듯 -> 빌드 컨텍스트에 포함되어 골치아픔

from dataclasses import dataclass
from enum import Enum


class PlatformCode(str, Enum):
    CHZZK = "chzzk"
    YOUTUBE = "youtube"
    SOOP = "sooplive"


class VODProcessingStatus(str, Enum):  # TODO: prefect 참고하여 수정 필요
    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태


class VODProcessingStepStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


# -------------- db init value -------------------------
@dataclass
class DBDefault:
    IS_ACTIVE = "true"

    VOD_PROCESSING_STATUS = VODProcessingStatus.PENDING.value

    class Len:
        ID = 256
        NAME = 256
        URL = 512


@dataclass
class AudioDataConstant:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_DTYPE_STR = "float32"
    ACODEC = "pcm_s32le"
    MAX_SPEECH_DURATION_S = 30


@dataclass
class MLModelPath:
    MODEL_BASE: str = "models"
    WHISPERX: str = f"{MODEL_BASE}/whisperx"


class EntryType(str, Enum):
    CHAT = "CHAT"
    DONATION = "DONATION"
    ASR = "ASR"


class ASRHallucinationFilter(str, Enum):
    NEWS = "뉴스"
    THANK_YOU_1 = "고맙습니다"
    THANK_YOU_2 = "감사합니다"
    WAS = "였습니다"
    MBC = "MBC"

    @classmethod
    def get_keywords(cls) -> list[str]:
        return [member.value for member in cls]


class LLMTask(str, Enum):
    SUMMARIZE = "summarize"
    META_SUMMARIZE = "meta_summarize"


@dataclass
class LLMPromptPath:
    SUMMARIZE: str = "stream/segment-analyzer"
    META_SUMMARIZE: str = "stream/context-integrator"


class StreamAtmosphere(str, Enum):
    SADNESS = "슬픔"
    NEUTRAL = "중립"
    HILARIOUS = "폭소"
    ANGER = "분노"
    ADMIRATION = "감탄"
    ANTICIPATION = "기대"


@dataclass
class StreamContextWindowSize:
    # entries의 timestamp에 대한 window size, 단위는 ms
    # CHUNK: int = 30 * 1000  채팅과 도네이션 이벤트를 기준으로 탐색할 때 길지도 짧지도 않아야 함
    SUMMARY: int = 300 * 1000
    META_SUMMARY: int = 3600 * 1000


@dataclass
class FileKeyTemplate:
    VIDEO = "{platform_code}/{video_no}/video.mp4"
    AUDIO = "{platform_code}/{video_no}/auido.wav"
    CHAT = "{platform_code}/{video_no}/chat_entries.jsonl"
    VAD_TIMESTAMP = "{platform_code}/{video_no}/vad_timestamp.jsonl"
    ASR = "{platform_code}/{video_no}/asr_entries.jsonl"
    SUMMARY_RAW = "{platform_code}/{video_no}/summary_raw.jsonl"
    SUMMARY = "{platform_code}/{video_no}/summaries.jsonl"
    META_SUMMARY = "{platform_code}/{video_no}/meta_summaries.jsonl"

    TMP_DIR = "{platform_code}/{video_no}/tmp"

    @classmethod
    def get_video_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.VIDEO.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_audio_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.AUDIO.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_chat_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.CHAT.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_vad_timestamp_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.VAD_TIMESTAMP.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_asr_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.ASR.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_summary_raw_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.SUMMARY_RAW.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_summary_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.SUMMARY.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_meta_summary_key(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.META_SUMMARY.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_tmp_dir(cls, platform_code: PlatformCode, video_no: str | int) -> str:
        return cls.TMP_DIR.format(platform_code=platform_code.value, video_no=video_no)


class VODProcessingStep(str, Enum):
    CRAWL_CHATS = "crawl_chats"
    DOWNLOAD_AUDIO = "download_audio"
    PERFORM_VAD = "perform_vad"
    PERFORM_ASR = "perform_asr"
    GENERATE_SUMMARY = "generate_summary"
    GENERATE_META_SUMMARY = "generate_meta_summary"
