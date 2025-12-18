from collections.abc import AsyncIterable, Iterable
from pathlib import Path
from typing import Any

import aiofiles
import orjson
from loguru import logger


class LocalStorage:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def get_absolute_path(self, key: str | Path) -> Path:
        """키를 받아 시스템 절대 경로를 반환합니다."""
        return self.base_dir / key

    async def ensure_parent_dir(self, key: str | Path) -> Path:
        full_path = self.get_absolute_path(key)
        directory = full_path.parent

        if not directory.exists():
            await self._mkdir_p(directory)
        return directory

    # [구분 유지] 폴더 생성용 (자기 자신 생성)
    async def create_dir(self, key: str | Path) -> Path:
        """
        키 경로 자체를 디렉토리로 생성합니다.
        (예: 'a/b/tmp' -> 'a/b/tmp/' 폴더 생성)
        """
        full_path = self.get_absolute_path(key)  # 통합된 메서드 사용

        if not full_path.exists():
            await self._mkdir_p(full_path)
        return full_path

    async def _mkdir_p(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Directory created: {path}")
        except Exception as e:
            if not path.exists():
                logger.error(f"❌ Failed to create directory {path}: {e}")
                raise

    async def write_jsonl(self, key: str | Path, data: list[dict[str, Any]]) -> Path:
        """
        Returns:
            Path: 실제로 저장된 파일의 절대 경로
        """
        await self.ensure_parent_dir(key)
        full_path = self.get_absolute_path(key)

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
        path = self.get_absolute_path(key)
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
        await self.ensure_parent_dir(key)
        path = self.get_absolute_path(key)

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
        path = self.get_absolute_path(key)
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


# 해당 vod에 대한 데이터 파이프라인이 완료되면 저장된 데이터를 전부 삭제해야함
# 모든 파일이 {platform_code}/{video_no}/ 아래에있으므로 해당 폴더를 삭제하는 것으로 해결
