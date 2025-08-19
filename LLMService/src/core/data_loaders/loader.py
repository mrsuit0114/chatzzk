from typing import Any

from core.data_loaders.base import BaseFetcher, BaseReader
from core.data_loaders.fetchers import DBFetcher, FsspecFetcher
from core.data_loaders.readers import JsonlReader, JsonReader
from core.enums import DataFormatType, DataSourceType


class DataLoader:
    """
    Fetcher와 Reader를 조합하여 데이터 로딩을 수행하는 메인 클래스.
    """

    def __init__(self):
        # 클래스가 아닌 인스턴스를 저장하여 재사용합니다.
        self._fetchers = {
            DataSourceType.LOCAL_FILE: FsspecFetcher(),
            DataSourceType.DATABASE: DBFetcher(),
        }
        self._readers = {
            DataFormatType.JSON: JsonReader(),
            DataFormatType.JSONL: JsonlReader(),
        }

    def _get_fetcher(self, source_type: DataSourceType) -> BaseFetcher:
        fetcher = self._fetchers.get(source_type)
        if not fetcher:
            raise ValueError(f"Unsupported data source type: {source_type.value}")
        return fetcher

    def _get_reader(self, format_type: DataFormatType) -> BaseReader:
        reader = self._readers.get(format_type)
        if not reader:
            raise ValueError(f"Unsupported data format type: {format_type.value}")
        return reader

    def load(
        self, source_type: DataSourceType, format_type: DataFormatType, source_identifier: str
    ) -> list[dict[str, Any]]:
        """
        지정된 소스와 포맷으로 데이터를 로드합니다.

        Args:
            source_type: 데이터를 가져올 소스 타입 (e.g., DataSourceType.LOCAL_FILE).
            format_type: 데이터의 포맷 타입 (e.g., DataFormatType.JSONL).
            source_identifier: 데이터 소스를 식별하는 문자열 (e.g., 파일 경로).

        Returns:
            최종적으로 파싱된 데이터 딕셔너리의 리스트.
        """
        fetcher = self._get_fetcher(source_type)
        reader = self._get_reader(format_type)

        raw_data = fetcher.fetch(source_identifier)
        parsed_data = reader.parse(raw_data)

        return parsed_data
