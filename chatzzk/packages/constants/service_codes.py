from enum import Enum


class WorkflowStatus(str, Enum):
    """
    VOD 처리 파이프라인의 전체적인 상태를 나타냅니다.
    """

    PENDING = "PENDING"  # 메타데이터 수집 완료, 처리 대기 중
    PROCESSING = "PROCESSING"  # 현재 처리 작업이 진행 중
    COMPLETED = "COMPLETED"  # 모든 처리 단계 성공적으로 완료
    FAILED = "FAILED"  # 처리 중 복구 불가능한 오류 발생


ASR_DUMMY_PAY_AMOUNT = 0
