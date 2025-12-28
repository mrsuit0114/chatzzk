from typing import Protocol


class BaseCloudStorage(Protocol):
    async def upload_file(self, local_path: str, remote_key: str, content_type: str = None) -> str:
        pass

    async def upload_directory(self, local_dir: str, remote_prefix: str) -> list[str]:
        pass
