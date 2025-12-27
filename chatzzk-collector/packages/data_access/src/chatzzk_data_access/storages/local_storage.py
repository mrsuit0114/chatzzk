from collections.abc import AsyncIterable, Iterable
from pathlib import Path
from typing import Any

import aiofiles
import orjson
from loguru import logger


class LocalStorage:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    # =========================================================
    # [Internal Method] 내부 연산용: Path 객체 반환
    # =========================================================
    def _resolve_path(self, key: str | Path) -> Path:
        """
        [내부용] 키를 받아 Path 객체를 반환합니다.
        파일 시스템 연산(.exists, .parent 등)을 위해 사용됩니다.
        """
        return self.base_dir / Path(key)

    async def _mkdir_p(self, path: Path) -> Path:
        """
        [내부용] Path 객체를 받아 디렉토리를 생성하고 Path를 반환합니다.
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Directory created: {path}")
            return path
        except Exception as e:
            if not path.exists():
                logger.error(f"❌ Failed to create directory {path}: {e}")
                raise
            return path

    # =========================================================
    # [External Method] 외부 노출용: str 입출력
    # =========================================================
    def get_absolute_path(self, key: str) -> str:
        """
        [외부용] 키를 받아 시스템 절대 경로를 문자열(str)로 반환합니다.
        """
        return str(self._resolve_path(key))

    async def ensure_parent_dir(self, key: str) -> str:
        """
        [외부용] 해당 키(파일)의 부모 디렉토리가 존재하는지 확인하고 생성합니다.
        """
        # 내부적으로는 Path 객체를 사용하여 .parent 속성과 .exists() 메서드 활용
        full_path: Path = self._resolve_path(key)
        directory: Path = full_path.parent

        if not directory.exists():
            await self._mkdir_p(directory)

        # 반환은 기준에 따라 str로 변환
        return str(directory)

    async def create_dir(self, key: str) -> str:
        """
        [외부용] 키 경로 자체를 디렉토리로 생성합니다.
        """
        full_path: Path = self._resolve_path(key)

        if not full_path.exists():
            await self._mkdir_p(full_path)

        return str(full_path)

    async def write_jsonl(self, key: str, data: list[dict[str, Any]]) -> str:
        """
        Returns:
            str: 실제로 저장된 파일의 절대 경로 (문자열)
        """
        # Path 객체로 로직 수행
        full_path: Path = self._resolve_path(key)

        # 부모 디렉토리 생성 로직 (내부 Path 활용)
        if not full_path.parent.exists():
            await self._mkdir_p(full_path.parent)

        try:
            lines = [orjson.dumps(item) for item in data]
            content = b"\n".join(lines)

            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)

            logger.debug(f"💾 Batch JSONL saved to: {full_path} (rows={len(data)})")
            return str(full_path)

        except Exception as e:
            logger.error(f"❌ Failed to write batch JSONL to {full_path}: {e}")
            raise

    async def read_jsonl(self, key: str) -> list[dict[str, Any]]:
        """
        [Batch] JSONL 파일을 통째로 읽어 리스트로 반환합니다.
        """
        path: Path = self._resolve_path(key)

        # Path 객체이므로 .exists() 사용 가능
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

    async def write_jsonl_stream(self, key: str, data_iterator: Iterable[dict] | AsyncIterable[dict]) -> str:
        """
        [Stream] 제너레이터를 받아 한 줄씩 씁니다.
        """
        path: Path = self._resolve_path(key)

        # 부모 디렉토리 확인
        if not path.parent.exists():
            await self._mkdir_p(path.parent)

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
            return str(path)

        except Exception as e:
            logger.error(f"❌ Failed to write stream JSONL to {path}: {e}")
            raise

    async def read_jsonl_stream(self, key: str) -> AsyncIterable[dict[str, Any]]:
        """
        [Stream] 파일을 한 줄씩 읽어 yield 합니다.
        """
        path: Path = self._resolve_path(key)

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

    async def append_jsonl(self, key: str, data: dict[str, Any]) -> str:
        """
        Returns:
            str: 저장된 파일의 절대 경로 (문자열)
        """
        full_path: Path = self._resolve_path(key)

        # 파일이 없을 경우 부모 디렉토리 생성 및 파일 생성 준비
        if not full_path.exists():
            if not full_path.parent.exists():
                await self._mkdir_p(full_path.parent)

        try:
            line = orjson.dumps(data) + b"\n"

            async with aiofiles.open(full_path, "ab") as f:
                await f.write(line)

            # 기존 코드에서는 Path를 반환했으나, 기준에 맞춰 str 반환으로 변경
            return str(full_path)

        except Exception as e:
            logger.error(f"❌ Failed to append JSONL to {full_path}: {e}")
            raise

    async def count_jsonl_lines(self, key: str) -> int:
        """
        파일의 라인 수(레코드 수)를 반환합니다.
        """
        full_path: Path = self._resolve_path(key)

        # Path 객체이므로 .exists() 호출 가능
        if not full_path.exists():
            return 0

        count = 0
        chunk_size = 1024 * 1024

        async with aiofiles.open(full_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                count += chunk.count(b"\n")

        return count

    async def write_json(self, key: str, data: dict[str, Any]) -> str:
        """
        Returns:
            str: 저장된 파일의 절대 경로 (문자열)
        """
        full_path: Path = self._resolve_path(key)

        # 부모 디렉토리 확인
        if not full_path.parent.exists():
            await self._mkdir_p(full_path.parent)

        try:
            content = orjson.dumps(data)

            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)

            logger.debug(f"💾 JSON saved to: {full_path}")
            return str(full_path)

        except Exception as e:
            logger.error(f"❌ Failed to write JSON to {full_path}: {e}")
            raise


# 해당 vod에 대한 데이터 파이프라인이 완료되면 저장된 데이터를 전부 삭제해야함
# 모든 파일이 {platform_code}/{video_no}/ 아래에있으므로 해당 폴더를 삭제하는 것으로 해결
