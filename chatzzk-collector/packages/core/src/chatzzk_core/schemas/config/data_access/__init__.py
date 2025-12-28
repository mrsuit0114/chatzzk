from pydantic import BaseModel

from .cloud_storage import CloudStorageConfig
from .database import DatabaseConfig


class DataAccessConfig(BaseModel):
    db: DatabaseConfig
    tmp_storage_base_dir: str
    cloud_storage: CloudStorageConfig


__all__ = ["DataAccessConfig", "DatabaseConfig", "CloudStorageConfig"]
