from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    db_implementation: str
    database_url: str


class LocalFileSystemStorageConfig(BaseModel):
    base_dir: str


class DataAccessConfig(BaseModel):
    db: DatabaseConfig
    tmp_storage: LocalFileSystemStorageConfig
