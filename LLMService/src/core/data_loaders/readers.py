from typing import Any

import orjson

from core.data_loaders.base import BaseReader


class JsonReader(BaseReader):
    """
    JSON 형식의 문자열을 orjson을 사용하여 파싱합니다.
    """

    def parse(self, raw_data: str) -> list[dict[str, Any]]:
        try:
            parsed = orjson.loads(raw_data)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                raise ValueError("JSON data must be an object or an array of objects.")
        except orjson.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON: {e}")


class JsonlReader(BaseReader):
    """
    JSONL (JSON Lines) 형식의 문자열을 orjson을 사용하여 파싱합니다.
    """

    def parse(self, raw_data: str) -> list[dict[str, Any]]:
        data = []
        lines = raw_data.strip().split("\n")
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                data.append(orjson.loads(line))
            except orjson.JSONDecodeError:
                raise ValueError(f"Error decoding JSON on line {i + 1}")
        return data
