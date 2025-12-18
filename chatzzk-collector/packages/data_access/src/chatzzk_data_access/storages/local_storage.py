from collections.abc import AsyncIterable, Iterable
from pathlib import Path
from typing import Any

import aiofiles
import orjson
from loguru import logger


class LocalStorage:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def _get_full_path(self, key: str | Path) -> Path:
        """상대 경로를 받아 root_dir과 결합한 절대 경로를 반환"""
        return self.base_dir / key

    async def ensure_dir(self, key: str | Path) -> None:
        path = self._get_full_path(key)
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"📁 Directory created: {path.parent}")
            except Exception as e:
                # 동시성 이슈로 이미 생성되었을 수 있으므로 다시 체크
                if not path.parent.exists():
                    logger.error(f"❌ Failed to create directory {path.parent}: {e}")
                    raise

    async def write_jsonl(self, key: str | Path, data: list[dict[str, Any]]) -> Path:
        """
        Returns:
            Path: 실제로 저장된 파일의 절대 경로
        """
        await self.ensure_dir(key)
        full_path = self._get_full_path(key)

        try:
            lines = [orjson.dumps(item) for item in data]
            content = b"\n".join(lines)

            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)

            logger.debug(f"💾 Batch JSONL saved to: {full_path} (rows={len(data)})")
            return full_path

        except Exception as e:
            logger.error(f"❌ Failed to write batch JSONL to {full_path}: {e}")
            raise

    async def read_jsonl(self, key: str | Path) -> list[dict[str, Any]]:
        """
        [Batch] JSONL 파일을 통째로 읽어 리스트로 반환합니다.
        """
        path = self._get_full_path(key)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist.")

        try:
            data = []
            async with aiofiles.open(path, "rb") as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        data.append(orjson.loads(line))

            return data

        except Exception as e:
            logger.error(f"❌ Failed to read batch JSONL from {path}: {e}")
            raise

    async def write_jsonl_stream(self, key: str | Path, data_iterator: Iterable[dict] | AsyncIterable[dict]) -> Path:
        """
        [Stream] 제너레이터를 받아 한 줄씩 씁니다.
        동기(Iterable)와 비동기(AsyncIterable) 제너레이터 모두 지원합니다.
        """
        await self.ensure_dir(key)
        path = self._get_full_path(key)

        try:
            async with aiofiles.open(path, "wb") as f:
                if isinstance(data_iterator, AsyncIterable):
                    async for item in data_iterator:
                        line = orjson.dumps(item)
                        await f.write(line + b"\n")

                else:
                    for item in data_iterator:
                        line = orjson.dumps(item)
                        await f.write(line + b"\n")

            logger.debug(f"💾 Stream JSONL saved to: {path}")
            return path

        except Exception as e:
            logger.error(f"❌ Failed to write stream JSONL to {path}: {e}")
            raise

    async def read_jsonl_stream(self, key: str | Path) -> AsyncIterable[dict[str, Any]]:
        """
        [Stream] 파일을 한 줄씩 읽어 yield 합니다.
        호출하는 쪽에서도 'async for'를 사용해야 합니다.
        """
        path = self._get_full_path(key)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist.")

        try:
            async with aiofiles.open(path, "rb") as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield orjson.loads(line)
                    except orjson.JSONDecodeError:
                        logger.warning(f"⚠️ Skipping invalid JSON line in {path}")
                        continue

        except Exception as e:
            logger.error(f"❌ Failed to read stream JSONL from {path}: {e}")
            raise
