from typing import Annotated, Literal

from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    db_implementation: Literal["postgres"] = "postgres"
    database_url: str


DatabaseConfig = Annotated[
    PostgresConfig,
    Field(discriminator="db_implementation"),
]
