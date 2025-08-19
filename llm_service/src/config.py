import os

from common.buckets import BucketNames
from common.clients.storage import StorageConfig


class Config:
    class DataProcessor:
        PROMPT_CMD_TO_TYPE_CODE = {"chat": 100, "donation": 1000, "asr": 10000}

    class Minio:
        ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
        ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
        SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "adminadmin")
        SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

    def __init__(self):
        self.storage_config = StorageConfig(
            endpoint=self.Minio.ENDPOINT,
            access_key=self.Minio.ACCESS_KEY,
            secret_key=self.Minio.SECRET_KEY,
            secure=self.Minio.SECURE,
            default_bucket=BucketNames.VOD_CONTEXTS,
        )
