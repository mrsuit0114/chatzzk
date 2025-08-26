from pathlib import Path
from typing import Any

import orjson  # orjson이 없다면 import json
from loguru import logger


def load_json_from_file(file_path: str | Path) -> Any | None:
    """
    주어진 경로의 JSON 파일을 안전하게 로드하여 Python 객체로 반환합니다.

    - 파일이 없거나, JSON 디코딩에 실패하거나, 다른 예외 발생 시
      에러를 로깅하고 None을 반환합니다.

    Args:
        file_path (str | Path): 로드할 JSON 파일의 경로.

    Returns:
        Optional[Any]: 성공 시 파싱된 Python 객체 (dict, list 등), 실패 시 None.
    """
    path = Path(file_path)

    if not path.is_file():
        logger.warning(f"File not found: {path}")
        return None

    try:
        logger.info(f"Attempting to load JSON from: {path}")
        # 'rb' 모드로 열어 orjson이 바이트를 직접 처리하게 하는 것이 효율적
        with path.open("rb") as f:
            data = orjson.loads(f.read())

        logger.success(f"✅ Successfully loaded JSON from {path}")
        return data

    except orjson.JSONDecodeError as e:
        logger.error(f"❌ Failed to decode JSON from {path}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while reading {path}: {e}")
        return None
