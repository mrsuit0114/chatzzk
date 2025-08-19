from abc import ABC, abstractmethod
from typing import Any


class BaseFetcher(ABC):
    """
    데이터 소스에서 원본(raw) 데이터를 가져오는 클래스의 기본 인터페이스입니다.
    """

    @abstractmethod
    def fetch(self, source_identifier: str) -> str:
        """
        지정된 식별자를 사용하여 데이터 소스에서 원본 데이터를 가져옵니다.

        Args:
            source_identifier: 데이터 소스를 가리키는 식별자 (예: 파일 경로, URL, DB 쿼리).

        Returns:
            가져온 원본 데이터 (주로 문자열 형태).
        """
        pass


class BaseReader(ABC):
    """
    원본 데이터를 파싱하여 구조화된 파이썬 객체로 변환하는 클래스의 기본 인터페이스입니다.
    """

    @abstractmethod
    def parse(self, raw_data: str) -> list[dict[str, Any]]:
        """
        원본 데이터 문자열을 파싱합니다.

        Args:
            raw_data: Fetcher가 가져온 원본 데이터.

        Returns:
            파싱된 데이터 딕셔너리의 리스트.
        """
        pass
