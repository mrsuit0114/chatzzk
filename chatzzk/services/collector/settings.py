from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.schemas.ml_configs import ASRConfig, ASRHttpConfig, SileroVADConfig, VADConfig
from chatzzk.packages.schemas.storage_configs import MinioConfig, StorageConfig


class ChzzkApiSettings(BaseSettings):
    vod_url_template: str = Field(...)
    vod_info_url_template: str = Field(...)
    vod_chat_url_template: str = Field(...)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )
    channel_vods_url_template: str = Field(...)
    cookies_file_path: str | None = Field(default=None)


class CollectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_nested_delimiter="__")
    target_index_for_video_resolution: int = Field(0)
    temp_dir_base: str = Field(default="/var/tmp", description="임시 파일을 저장할 기본 디렉토리")

    chzzk_api: ChzzkApiSettings = Field(default_factory=ChzzkApiSettings)

    vad_model_config: VADConfig = Field(default_factory=SileroVADConfig)
    asr_model_config: ASRConfig = Field(default_factory=ASRHttpConfig)

    storage_config: StorageConfig = Field(default_factory=MinioConfig)


collector_settings = CollectorSettings()
