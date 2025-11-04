from dataclasses import dataclass
from enum import Enum


class PlatformCode(str, Enum):
    CHZZK = "chzzk"
    YOUTUBE = "youtube"
    SOOP = "sooplive"


# -------------- db init value -------------------------
@dataclass
class DBDefaults:
    # Platform
    PLATFORM_NAME_MAX_LEN = 100
    DONATION_UNIT_MAX_LEN = 50

    # Channel
    IS_ACTIVE_DEFAULT = "true"

    # ResultObjectKey
    OBJECT_KEY_MAX_LEN = 255


class LocalTempPath:
    VIDEO_FILE = "{video_no}/video.mp4"
    AUDIO_FILE = "{video_no}/audio.wav"
    TIMESTAMPS_FILE = "{video_no}/timestamps.json"


class Atmosphere(str, Enum):
    """요약된 window의 분위기를 표현합니다."""


# ---------------------- pipeline status --------------------------------
class VODProcessStatus(str, Enum):  # TODO: prefect 참고하여 수정 필요
    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태


class ResultObjectFileType(str, Enum):
    CHAT_ENTRIES = "CHAT_ENTRIES"
    ASR_ENTRIES = "ASR_ENTRIES"
    SUMMARIES = "SUMMARIES"
    META_SUMMARIES = "META_SUMMARIES"


class PipelineStep(str, Enum):
    """
    파이프라인의 세부 단계를 정의합니다.
    """

    CRAWL_CHAT = "crawl_chat"
    DOWNLOAD_VIDEO = "download_video"
    EXTRACT_WAV = "extract_wav"
    PERFORM_VAD = "perform_vad"
    PERFORM_ASR = "perform_asr"
    GENERATE_SUMMARIES = "generate_summaries"
    GENERATE_META_SUMMARIES = "generate_meta_summaries"


class StepStatus(str, Enum):  # TODO: prefect 작업할 떄 수정 필요
    COMPLETED = "COMPLETED"  # 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 단계가 실패한 상태


# -----------storage-----------------
@dataclass
class StorageObject:
    """스토리지의 오브젝트 이름/경로 템플릿을 정의합니다."""

    # 기본 파일명 상수
    VIDEO_FILE_NAME = "video.mp4"
    AUDIO_FILE_NAME = "audio.wav"
    TIMESTAMPS_FILE_NAME = "timestamps.json"
    CHAT_ENTRIES_FILE_NAME = "chat_entries.jsonl"
    ASR_ENTRIES_FILE_NAME = "asr_entries.jsonl"
    SUMMARY_ENTRIES_FILE_NAME = "summary_entries.jsonl"
    META_SUMMARY_ENTRIES_FILE_NAME = "meta_summary_entries.jsonl"

    # 임시 스토리지에 저장될 파일들 (재시작 시 이어받기 위함)
    TEMP_VIDEO = "temp/{video_no}/" + VIDEO_FILE_NAME
    TEMP_AUDIO = "temp/{video_no}/" + AUDIO_FILE_NAME
    TEMP_TIMESTAMPS = "temp/{video_no}/" + TIMESTAMPS_FILE_NAME

    # 영구 스토리지에 저장될 파일들 (웹 서버 접근용)
    CHAT_ENTRIES = "contexts/{video_no}/" + CHAT_ENTRIES_FILE_NAME
    ASR_ENTRIES = "contexts/{video_no}/" + ASR_ENTRIES_FILE_NAME
    SUMMARY_ENTRIES = "summaries/{video_no}/" + SUMMARY_ENTRIES_FILE_NAME
    META_SUMMARY_ENTRIES = "meta_summaries/{video_no}/" + META_SUMMARY_ENTRIES_FILE_NAME


# ----------- speech common config ----------------
MAX_SPEECH_DURATION_S = 30
MIN_SILENCE_DURATION_MS = 500
SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_DTYPE_STR = "float32"
