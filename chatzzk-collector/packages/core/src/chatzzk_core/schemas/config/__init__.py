from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .clients import ClientsConfig
from .data_access import DataAccessConfig
from .services import ServicesConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file="test.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    clients: ClientsConfig
    data_access: DataAccessConfig
    services: ServicesConfig = Field(default_factory=ServicesConfig)


__all__ = ["Settings", "ClientsConfig", "DataAccessConfig", "ServicesConfig"]
