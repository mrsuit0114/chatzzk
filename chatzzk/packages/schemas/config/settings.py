from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk.packages.schemas.config.clients.http import AioHTTPConfig
from chatzzk.packages.schemas.config.clients.media_processor import MediaProcessorConfig
from chatzzk.packages.schemas.config.clients.ml import ASRConfig, VADConfig
from chatzzk.packages.schemas.config.data_access.database import DatabaseConfig
from chatzzk.packages.schemas.config.services.vod_discovery import VODDiscoveryServiceConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # 예: DB__DATABASE_URL
        env_file="local.test.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseConfig
    asr: ASRConfig
    vad: VADConfig
    aiohttp: AioHTTPConfig = (
        AioHTTPConfig()
    )  # .env에서 주입되지않고 상수만 적용한 필드의 경우 인스턴스를 직접 생성해서 주입해야함
    chzzk_api: ChzzkAPIConfig
    media_processor: MediaProcessorConfig = MediaProcessorConfig()

    vod_discovery_service: VODDiscoveryServiceConfig = Field(default_factory=VODDiscoveryServiceConfig)
