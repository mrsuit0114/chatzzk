from abc import ABC, abstractmethod

from chatzzk.packages.schemas.data_models import StreamContextEntry


class StorageInterface(ABC):
    """
    모든 영구 스토리지 관리자가 구현해야 하는 인터페이스입니다.
    """

    @abstractmethod
    def save_context(self, video_no: str, video_context: list[StreamContextEntry]) -> str:
        """
        주어진 컨텍스트 스트림을 영구 스토리지에 저장하고,
        저장된 최종 경로 또는 URI를 반환합니다.
        Returns:
            str: 저장된 파일의 고유 식별자 (e.g., 'context/12345.jsonl', 's3://bucket/context/12345.jsonl').
        """
        pass

    @abstractmethod
    def load_context(self, video_no: str) -> list[StreamContextEntry] | None:
        pass

    # @abstractmethod
    # def save_summary(self, video_no: str, summary_data: dict) -> str: ...
