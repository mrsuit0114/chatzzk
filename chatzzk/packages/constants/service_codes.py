from enum import Enum


class WorkflowStatus(str, Enum):
    """
    VOD 처리 파이프라인의 전체적인 상태를 나타냅니다.
    """

    PENDING_PREPROCESSING = "PENDING_PREPROCESSING"  # 메타데이터 수집 완료, 전처리 대기

    PREPROCESSING_IN_PROGRESS = "PREPROCESSING_IN_PROGRESS"  # 채팅, MP4 등 원본 데이터 수집 중
    PENDING_PROCESSING = "PENDING_PROCESSING"  # 필요한 데이터 로컬 저장 완료 - chat.jsonl, mp4

    PROCESSING_IN_PROGRESS = "PROCESSING_IN_PROGRESS"  # WAV추출 -> VAD, ASR 수행 -> asr_context 구성 -> chat_context와 asr_context 병합하여 video_context 생성 및 저장완료
    PENDING_POSTPROCESSING = "PENDING_POSTPROCESSING"  # 핵심 처리 완료, 요약 등 후처리 대기

    POSTPROCESSING_IN_PROGRESS = "POSTPROCESSING_IN_PROGRESS"  # 요약 등 후처리 진행 중
    COMPLETED = "COMPLETED"

    FAILED = "FAILED"


ASR_DUMMY_PAY_AMOUNT = 0
