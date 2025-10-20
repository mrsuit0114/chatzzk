from typing import Protocol


class VodManagement(Protocol):
    """
    개별 'VOD'에 대한 예외적인 관리 작업을 정의합니다.
    """

    def reprocess_vod(self, video_no: str) -> None:
        """
        특정 VOD의 처리 상태를 다시 'PENDING'으로 변경하여,
        파이프라인이 재처리하도록 합니다.
        """
        ...

    def exclude_vod_from_analysis(self, video_no: str) -> None:
        """
        특정 VOD를 분석 및 요약 대상에서 영구적으로 제외합니다.
        """
        ...
