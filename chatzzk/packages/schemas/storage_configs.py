from typing import Annotated, Literal

from pydantic import BaseModel, Field

from chatzzk.packages.constants.service_codes import StorageBucket


class MinioConfig(BaseModel):
    storage_implementation: Literal["minio"] = "minio"
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str = Field(StorageBucket.CHZZK.value)
    secure: bool = False


StorageConfig = Annotated[
    MinioConfig,  # | S3Config,
    Field(discriminator="storage_implementation"),
]
