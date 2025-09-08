from typing import Annotated, Literal

from pydantic import BaseModel, Field


class MinioConfig(BaseModel):
    storage_implementation: Literal["minio"] = "minio"
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str
    secure: bool = False


StorageConfig = Annotated[
    MinioConfig,  # | S3Config,
    Field(discriminator="storage_implementation"),
]
