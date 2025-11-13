from dataclasses import dataclass
from enum import Enum


class PlatformCode(str, Enum):
    CHZZK = "chzzk"
    YOUTUBE = "youtube"
    SOOP = "sooplive"


# -------------- db init value -------------------------
@dataclass
class DBDefault:
    DEFAULT_STRING_MAX_LEN_SHORT = 64
    DEFAULT_STRING_MAX_LEN_MEDIUM = 255
    DEFAULT_STRING_MAX_LEN_LONG = 1024

    # Channel
    IS_ACTIVE_DEFAULT = "true"


@dataclass
class AudioDataConstant:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_DTYPE_STR = "float32"
    ACODEC = "pcm_s32le"
    MAX_SPEECH_DURATION_S = 30


class FileFormat(str, Enum):
    JSONL = "jsonl"
    MP4 = "mp4"
    WAV = "wav"


@dataclass
class MLModelPath:
    WHISPERX = "models/whisperx"


@dataclass
class FileKeyTemplate:
    VIDEO = "{platform_code}/{video_no}/video.mp4"
    AUDIO = "{platform_code}/{video_no}/auido.wav"
    CHAT = "{platform_code}/{video_no}/chat_entries.jsonl"
    VAD_TIMESTAMP = "{platform_code}/{video_no}/vad_timestamp.jsonl"
    ASR = "{platform_code}/{video_no}/asr_entries.jsonl"
    SUMMARY = "{platform_code}/{video_no}/summaries.jsonl"
    META_SUMMARY = "{platform_code}/{video_no}/meta_summaries.jsonl"

    TMP_DIR = "{platform_code}/{video_no}/tmp"

    @classmethod
    def get_video_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.VIDEO.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_audio_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.AUDIO.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_chat_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.CHAT.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_vad_timestamp_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.VAD_TIMESTAMP.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_asr_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.ASR.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_summary_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.SUMMARY.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_meta_summary_key(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.META_SUMMARY.format(platform_code=platform_code.value, video_no=video_no)

    @classmethod
    def get_tmp_dir(cls, platform_code: PlatformCode, video_no: int) -> str:
        return cls.TMP_DIR.format(platform_code=platform_code.value, video_no=video_no)


class VODProcessingStep(str, Enum):
    CRAWL_CHATS = "crawl_chats"
    DOWNLOAD_AUDIO = "download_audio"
    PERFORM_VAD = "perform_vad"
    PERFORM_ASR = "perform_asr"
    GENERATE_SUMMARIES = "generate_summaries"
    GENERATE_META_SUMMARIES = "generate_meta_summaries"


class VODProcessingStepStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class ResultObjectFileType(str, Enum):
    CHAT_ENTRIES = "CHAT_ENTRIES"
    ASR_ENTRIES = "ASR_ENTRIES"
    SUMMARIES = "SUMMARIES"
    META_SUMMARIES = "META_SUMMARIES"


class VODProcessStatus(str, Enum):  # TODO: prefect 참고하여 수정 필요
    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태


# class LocalTempPath:
#     VIDEO_FILE = "{video_no}/video.mp4"
#     AUDIO_FILE = "{video_no}/audio.wav"
#     TIMESTAMPS_FILE = "{video_no}/timestamps.json"


# class Atmosphere(str, Enum):
#     """요약된 window의 분위기를 표현합니다."""


# class PipelineStep(str, Enum):
#     """
#     파이프라인의 세부 단계를 정의합니다.
#     """

#     CRAWL_CHAT = "crawl_chat"
#     DOWNLOAD_VIDEO = "download_video"
#     EXTRACT_WAV = "extract_wav"
#     PERFORM_VAD = "perform_vad"
#     PERFORM_ASR = "perform_asr"
#     GENERATE_SUMMARIES = "generate_summaries"
#     GENERATE_META_SUMMARIES = "generate_meta_summaries"


# class StepStatus(str, Enum):  # TODO: prefect 작업할 떄 수정 필요
#     COMPLETED = "COMPLETED"  # 단계가 성공적으로 완료된 상태
#     FAILED = "FAILED"  # 단계가 실패한 상태


# # -----------storage-----------------
# @dataclass
# class StorageObject:
#     """스토리지의 오브젝트 이름/경로 템플릿을 정의합니다."""

#     # 기본 파일명 상수
#     VIDEO_FILE_NAME = "video.mp4"
#     AUDIO_FILE_NAME = "audio.wav"
#     TIMESTAMPS_FILE_NAME = "timestamps.json"
#     CHAT_ENTRIES_FILE_NAME = "chat_entries.jsonl"
#     ASR_ENTRIES_FILE_NAME = "asr_entries.jsonl"
#     SUMMARY_ENTRIES_FILE_NAME = "summary_entries.jsonl"
#     META_SUMMARY_ENTRIES_FILE_NAME = "meta_summary_entries.jsonl"

#     # 임시 스토리지에 저장될 파일들 (재시작 시 이어받기 위함)
#     TEMP_VIDEO = "temp/{video_no}/" + VIDEO_FILE_NAME
#     TEMP_AUDIO = "temp/{video_no}/" + AUDIO_FILE_NAME
#     TEMP_TIMESTAMPS = "temp/{video_no}/" + TIMESTAMPS_FILE_NAME

#     # 영구 스토리지에 저장될 파일들 (웹 서버 접근용)
#     CHAT_ENTRIES = "contexts/{video_no}/" + CHAT_ENTRIES_FILE_NAME
#     ASR_ENTRIES = "contexts/{video_no}/" + ASR_ENTRIES_FILE_NAME
#     SUMMARY_ENTRIES = "summaries/{video_no}/" + SUMMARY_ENTRIES_FILE_NAME
#     META_SUMMARY_ENTRIES = "meta_summaries/{video_no}/" + META_SUMMARY_ENTRIES_FILE_NAME
