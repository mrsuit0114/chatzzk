from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    db_implementation: str
    database_url: str
    pool_size: int
    max_overflow: int
