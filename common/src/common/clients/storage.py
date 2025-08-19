import io
from abc import ABC, abstractmethod
from typing import Optional, Union

from loguru import logger
from minio import Minio
from pydantic import BaseModel


class StorageConfig(BaseModel):
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool = True
    default_bucket: Optional[str] = None


class StorageClient(ABC):
    @abstractmethod
    def upload(self, object_name: str, data: Union[bytes, str], bucket_name: Optional[str] = None) -> None:
        """Uploads data to the storage."""
        pass

    @abstractmethod
    def download(self, object_name: str, bucket_name: Optional[str] = None) -> bytes:
        """Downloads data from the storage."""
        pass


class MinioStorageClient(StorageClient):
    def __init__(self, config: StorageConfig):
        self.config = config
        try:
            self.client = Minio(
                endpoint=config.endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                secure=config.secure,
            )
            logger.info("✅ MinIO client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MinIO client: {e}")
            raise

    def _get_bucket(self, bucket_name: Optional[str] = None) -> str:
        target_bucket = bucket_name or self.config.default_bucket
        if not target_bucket:
            raise ValueError("Bucket name must be provided or set as a default in the config.")
        return target_bucket

    def upload(self, object_name: str, data: Union[bytes, str], bucket_name: Optional[str] = None) -> None:
        target_bucket = self._get_bucket(bucket_name)

        if isinstance(data, str):
            data = data.encode("utf-8")

        data_stream = io.BytesIO(data)
        data_len = len(data)

        try:
            found = self.client.bucket_exists(target_bucket)
            if not found:
                self.client.make_bucket(target_bucket)
                logger.info(f"Bucket '{target_bucket}' created.")

            self.client.put_object(
                bucket_name=target_bucket,
                object_name=object_name,
                data=data_stream,
                length=data_len,
                content_type="application/octet-stream",
            )
            logger.info(f"Successfully uploaded '{object_name}' to bucket '{target_bucket}'.")
        except Exception as e:
            logger.error(f"❌ Failed to upload '{object_name}': {e}")
            raise

    def download(self, object_name: str, bucket_name: Optional[str] = None) -> bytes:
        target_bucket = self._get_bucket(bucket_name)
        response = None
        try:
            response = self.client.get_object(target_bucket, object_name)
            content = response.read()
            logger.info(f"Successfully downloaded '{object_name}' from bucket '{target_bucket}'.")
            return content
        except Exception as e:
            logger.error(f"❌ Failed to download '{object_name}': {e}")
            raise
        finally:
            if response:
                response.close()
                response.release_conn()
