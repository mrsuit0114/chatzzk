from typing import IO, TypeVar

import orjson
from loguru import logger
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_jsonl_as_models(file_handle: IO, model_type: type[T]) -> list[T]:
    """
    열려있는 jsonl 파일 핸들(바이트 모드)을 읽어 Pydantic 모델 객체 리스트로 반환합니다.
    """
    entries = []
    for line in file_handle:
        if line.strip():
            try:
                data = orjson.loads(line)
                entries.append(model_type.model_validate(data))
            except (orjson.JSONDecodeError, Exception) as e:
                logger.warning(f"Skipping invalid line in jsonl file: {line.strip()}. Error: {e}")
    return entries
