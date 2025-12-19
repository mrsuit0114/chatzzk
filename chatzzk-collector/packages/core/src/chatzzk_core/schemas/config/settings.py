from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk_core.schemas.config.clients.client import ClientsConfig
from chatzzk_core.schemas.config.data_access.data_access import DataAccessConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file="test.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    clients: ClientsConfig
    data_access: DataAccessConfig
