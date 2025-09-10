from enum import Enum, IntEnum


class VodProcessStatus(str, Enum):
    """
    VOD 처리 파이프라인의 전체적인 상태를 나타냅니다.
    세부 단계는 status_details (JSONB) 필드에서 관리합니다.
    """

    PENDING = "PENDING"  # 모든 처리를 기다리는 초기 상태
    PROCESSING = "PROCESSING"  # 하나 이상의 파이프라인 단계가 진행 중인 상태
    COMPLETED = "COMPLETED"  # 모든 파이프라인 단계가 성공적으로 완료된 상태
    FAILED = "FAILED"  # 하나 이상의 필수 파이프라인 단계가 실패한 상태


class TempFile:
    VIDEO = "video.mp4"
    AUDIO = "audio.wav"
    CHAT_CONTEXT = "chat_context.jsonl"
    ASR_CONTEXT = "asr_context.jsonl"


class StorageObject:
    """영구 스토리지의 오브젝트 이름/경로 템플릿을 정의합니다."""

    # format() 메서드를 사용하여 경로를 생성: StorageObject.VOD_CONTEXT.format(video_no=123)
    VIDEO_CONTEXT = "contexts/{video_no}.jsonl"
    VIDEO_SUMMARY = "summaries/{video_no}.jsonl"
    # VIDEO_SUMMARY_META = "meta-summaries/{video_no}.jsonl"


class StorageBucket:
    CHZZK = "chzzk"


class ContextType(IntEnum):
    CHAT = 100
    DONATION = 1000
    ASR = 10000


ASR_DUMMY_PAY_AMOUNT = 0

MAX_SPEECH_DURAION_S = 30
SAMPLE_RATE = 16000
