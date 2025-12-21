from pydantic import BaseModel

from .database import DatabaseConfig


class DataAccessConfig(BaseModel):
    db: DatabaseConfig
    tmp_storage_base_dir: str


__all__ = ["DataAccessConfig", "DatabaseConfig"]
