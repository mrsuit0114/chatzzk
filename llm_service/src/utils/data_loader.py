import orjson
from common.clients.storage import MinioStorageClient
from common.schemas.context_data import ContextData
from loguru import logger


class DataLoader:
    """Responsible for fetching and validating data from a source."""

    def __init__(self, storage_client: MinioStorageClient):
        self.storage = storage_client

    def _parse_and_validate_contexts(self, data_bytes: bytes) -> list[ContextData]:
        """Parses bytes into a list of validated ContextData objects."""
        contexts = []
        try:
            jsonl_string = data_bytes.decode("utf-8")
            lines = jsonl_string.strip().splitlines()
            for line in lines:
                if not line:
                    continue
                try:
                    json_object = orjson.loads(line)
                    contexts.append(ContextData(**json_object))
                except orjson.JSONDecodeError as e:
                    logger.warning(f"JSON parsing error: {e} - Line: '{line}'")
                except Exception as e:
                    logger.warning(f"Pydantic validation error: {e} - Line: '{line}'")
            return contexts
        except Exception as e:
            logger.error(f"Failed to process data bytes: {e}")
            return []

    def get_contexts_from_jsonl(self, video_no: int) -> list[ContextData]:
        """
        Fetches a JSONL file from storage, validates its content,
        and returns a sorted list of ContextData objects.
        """
        file_path = f"{video_no}.jsonl"
        try:
            downloaded_bytes = self.storage.download(file_path)
            if not downloaded_bytes:
                logger.warning(f"File is empty or does not exist: {file_path}")
                return []
        except Exception as e:
            logger.error(f"Failed to download {file_path}: {e}")
            return []

        contexts = self._parse_and_validate_contexts(downloaded_bytes)
        return contexts
