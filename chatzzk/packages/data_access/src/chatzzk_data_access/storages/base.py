from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterable


class PipelineStorage(ABC):
    @abstractmethod
    async def save_jsonl(self, key: str, data_iter: AsyncIterable[dict]) -> str: ...

    @abstractmethod
    async def append_jsonl(self, key: str, data_iter: AsyncIterable[dict]) -> str: ...

    @abstractmethod
    async def load_jsonl(self, key: str) -> AsyncGenerator[dict, None]: ...

    @abstractmethod
    def get_path(self, key: str) -> str: ...

    @abstractmethod
    def get_or_create_path(self, key: str, is_dir: bool) -> str: ...

    # @abstractmethod
    # async def load(self, path: str) -> bytes:
    #     ...

    # @abstractmethod
    # async def delete(self, path: str) -> None:
    #     ...

    # @abstractmethod
    # async def exists(self, path: str) -> bool:
    #     ...


# class ServiceStorage(ABC): ...
