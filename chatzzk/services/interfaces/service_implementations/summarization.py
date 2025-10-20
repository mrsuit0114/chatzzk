from typing import Protocol


class Summarization(Protocol):
    """
    분석된 데이터를 바탕으로 요약본을 생성하는 역할을 정의합니다.
    """

    def generate_summaries(self, video_no: str) -> str:
        """
        채팅과 ASR 결과를 기반으로 시간대별 요약을 생성하고,
        영구 스토리지에 저장한 뒤 경로(key)를 반환합니다.
        """
        ...

    def generate_meta_summary(self, video_no: str) -> str:
        """
        시간대별 요약을 바탕으로 방송 전체의 메타 요약을 생성하고,
        영구 스토리지에 저장한 뒤 경로(key)를 반환합니다.
        """
        ...
