from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.schemas.config.api import APIClientConfig
from chatzzk.packages.schemas.config.database import DatabaseConfig
from chatzzk.packages.schemas.config.discovery import DiscoveryServiceConfig
from chatzzk.packages.schemas.config.ml import ASRConfig, VADConfig
from chatzzk.packages.schemas.config.storage import StorageConfig


class Settings(BaseSettings):
    """
    애플리케이션의 모든 설정을 통합 관리하는 최상위 모델입니다.
    .env 파일, 환경 변수 등에서 설정을 계층적으로 로드합니다.
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # 예: DB__DATABASE_URL
        env_file="local.test.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db: DatabaseConfig
    storage: StorageConfig
    asr: ASRConfig
    vad: VADConfig
    api: APIClientConfig

    discovery_service: DiscoveryServiceConfig = Field(default_factory=DiscoveryServiceConfig)
