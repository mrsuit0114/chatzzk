from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    db_implementation: str
    database_url: str
