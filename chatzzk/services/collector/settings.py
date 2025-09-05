import tempfile

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.schemas.ml_configs import SileroVADConfig, VADConfig


class ChzzkApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    """치지직 플랫폼 API와 관련된 설정을 관리합니다."""

    chzzk_vod_url_template: str = Field(...)
    chzzk_vod_info_url_template: str = Field(...)
    chzzk_vod_chat_url_template: str = Field(...)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )
    chzzk_channel_vods_url_template: str = Field(...)
    chzzk_cookies_file_path: str | None = Field(default=None)


class CollectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    target_index_for_video_resolution: int = Field(0)
    temp_dir_base: str = Field(default_factory=tempfile.gettempdir, description="임시 파일을 저장할 기본 디렉토리")

    asr_inference_server_url: str = Field(...)
    vad_model_config: VADConfig = Field(default_factory=SileroVADConfig)


# 설정 객체를 싱글톤처럼 생성하여 다른 모듈에서 import하여 사용할 수 있도록 함
chzzk_api_settings = ChzzkApiSettings()
collector_settings = CollectorSettings()
