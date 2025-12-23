from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    database_url: str
    pool_size: int
    max_overflow: int
