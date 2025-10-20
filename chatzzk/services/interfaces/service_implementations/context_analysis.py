from typing import Protocol


class ContextAnalysis(Protocol):
    """
    수집된 원본 데이터(채팅, ASR 결과)를 분석하여 통계 정보를 추출하고
    데이터베이스에 저장하는 역할을 정의합니다.
    """

    def analyze_and_aggregate_context(self, video_no: str) -> None:
        """
        'chat_entries.jsonl'과 'asr_entries.jsonl' 파일의 내용을 집계하고 분석합니다.
        분석된 통계 결과를 데이터베이스의 분석(analytics) 테이블에 업데이트합니다.
        """
        ...
