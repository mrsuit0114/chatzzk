from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.schemas.config.clients.client import ClientsConfig
from chatzzk.packages.schemas.config.data_access.data_access import DataAccessConfig
from chatzzk.packages.schemas.config.services.vod_discovery import VODDiscoveryServiceConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # 예: DB__DATABASE_URL
        env_file="local.test.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_access: DataAccessConfig
    clients: ClientsConfig

    vod_discovery_service: VODDiscoveryServiceConfig = Field(default_factory=VODDiscoveryServiceConfig)
