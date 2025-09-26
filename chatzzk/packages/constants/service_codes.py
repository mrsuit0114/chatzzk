import datetime
from enum import Enum, IntEnum


# ----------db--------------
class VodProcessStatus(str, Enum):
    """
    VOD 처리 파이프라인의 전체적인 상태를 나타냅니다.
    세부 단계는 status_details (JSONB) 필드에서 관리합니다.
    """

    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태
    PERMANENTLY_FAILED = "PERMANENTLY_FAILED"  # 여러 번의 재시도 끝에 영구적으로 실패로 처리된 상태


class ChzzkMessageTypeCode(IntEnum):
    CHAT = 1
    DONATION = 10
    SYSTEM = 30


class SubscriptionTier(IntEnum):
    NO_SUBSCRIPTION = 0
    GENERAL = 1
    PREMIUM = 2


class OsType(str, Enum):
    IOS = "IOS"
    PC = "PC"
    AOS = "AOS"


class UserRoleCode(str, Enum):
    COMMON_USER = "common_user"
    STREAMING_CHAT_MANAGER = "streaming_chat_manager"
    STREAMING_CHANNEL_OWNER = "streaming_channel_owner"
    STREAMING_CHANNEL_MANAGER = "streaming_channel_manager"


class Atmosphere(str, Enum):
    """요약된 window의 분위기를 표현합니다."""

    # TODO: 사용자가 직접 항목을 추가할 예정
    pass


class PipelineStep(str, Enum):
    """
    파이프라인의 세부 단계를 정의합니다.
    """

    CRAWL_CHAT = "crawl_chat"
    DOWNLOAD_VIDEO = "download_video"
    EXTRACT_WAV = "extract_wav"
    PERFORM_ASR = "perform_asr"


class StepStatus(str, Enum):
    """
    세부 단계의 상태를 정의합니다.
    """

    COMPLETED = "COMPLETED"  # 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 단계가 실패한 상태


# ------------workspace------------------
class TempFile:
    VIDEO = "video.mp4"
    AUDIO = "audio.wav"
    CHAT_CONTEXT = "chat_context.jsonl"
    ASR_CONTEXT = "asr_context.jsonl"


# -----------storage-----------------
class StorageObject:
    """영구 스토리지의 오브젝트 이름/경로 템플릿을 정의합니다."""

    # format() 메서드를 사용하여 경로를 생성: StorageObject.VOD_CONTEXT.format(video_no=123)
    VIDEO_CONTEXT = "contexts/{video_no}.jsonl"
    VIDEO_SUMMARY = "summaries/{video_no}.jsonl"
    # VIDEO_SUMMARY_META = "meta-summaries/{video_no}.jsonl"


class StorageBucket(str, Enum):
    CHZZK = "chzzk"


# ---------------service----------------
class ContextType(IntEnum):
    CHAT = 100
    DONATION = 1000
    ASR = 10000


START_DATE = datetime.date(2025, 1, 1)

ASR_DUMMY_PAY_AMOUNT = 0


# ----------- speech common config ----------------
MAX_SPEECH_DURAION_S = 30
SAMPLE_RATE = 16000
