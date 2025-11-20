from collections.abc import AsyncGenerator, AsyncIterable
from pathlib import Path

import aiofiles
import orjson

from chatzzk_data_access.storages.base import PipelineStorage


class LocalFileSystemStorage(PipelineStorage):
    """
    Local file system 기반 스토리지의 책임과 역할:
    - 직렬화 가능한 데이터(jsonl 등)의 저장 및 로딩 기능을 제공
    - 내부적으로 파일 경로 관리(_get_absolute_path)
    - FileFormat에 따라 입출력 방식 정의 및 확장
    """

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_or_create_path(self, key: str, is_dir: bool = False) -> str:
        abs_path = self.base_dir / key
        if is_dir:
            abs_path.mkdir(parents=True, exist_ok=True)
        else:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
        return str(abs_path)

    async def _write_jsonl(self, path: Path, items: AsyncIterable[dict]) -> None:
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            async for obj in items:
                line = orjson.dumps(obj, option=orjson.OPT_APPEND_NEWLINE).decode("utf-8")
                await f.write(line)

    async def _read_jsonl(self, path: Path) -> AsyncGenerator[dict, None]:
        async def generator() -> AsyncGenerator[dict, None]:
            async with aiofiles.open(path, encoding="utf-8") as f:
                async for line in f:
                    if line.strip():
                        yield orjson.loads(line)

        return generator()

    async def save_jsonl(self, key: str, data_iter: AsyncIterable[dict]) -> str:
        path = self.get_or_create_path(key)
        await self._write_jsonl(path, data_iter)
        return str(path)

    async def load_jsonl(self, key: str) -> AsyncGenerator[dict, None]:
        path = self.get_path(key)
        if not Path(path).is_file():
            raise FileNotFoundError(f"File not found at {path}")
        return await self._read_jsonl(Path(path))

    def get_path(self, key: str) -> str:
        return str(self.base_dir / key)
