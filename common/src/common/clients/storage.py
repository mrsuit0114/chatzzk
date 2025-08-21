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


class StorageClient(ABC):
    @abstractmethod
    def upload(self, object_name: str, data: Union[bytes, str], bucket_name: str) -> None:
        """Uploads data to the storage."""
        pass

    @abstractmethod
    def download(self, object_name: str, bucket_name: str) -> bytes:
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

    def upload(self, object_name: str, data: Union[bytes, str], bucket_name: str) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8")

        data_stream = io.BytesIO(data)
        data_len = len(data)

        try:
            found = self.client.bucket_exists(bucket_name)
            if not found:
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' created.")

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data_stream,
                length=data_len,
                content_type="application/octet-stream",
            )
            logger.info(f"Successfully uploaded '{object_name}' to bucket '{bucket_name}'.")
        except Exception as e:
            logger.error(f"❌ Failed to upload '{object_name}': {e}")
            raise

    def download(self, object_name: str, bucket_name: Optional[str] = None) -> bytes:
        response = None
        try:
            response = self.client.get_object(bucket_name, object_name)
            content = response.read()
            logger.info(f"Successfully downloaded '{object_name}' from bucket '{bucket_name}'.")
            return content
        except Exception as e:
            logger.error(f"❌ Failed to download '{object_name}': {e}")
            raise
        finally:
            if response:
                response.close()
                response.release_conn()
