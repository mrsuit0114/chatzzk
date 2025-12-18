from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    db_implementation: str
    database_url: str


class DataAccessConfig(BaseModel):
    db: DatabaseConfig
    tmp_storage_base_dir: str
