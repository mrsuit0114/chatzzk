import tempfile

from pydantic import Field
from pydantic_settings import BaseSettings


class ChzzkApiSettings(BaseSettings):
    """치지직 플랫폼 API와 관련된 설정을 관리합니다."""

    CHZZK_VOD_URL_TEMPLATE: str = Field(...)
    CHZZK_VOD_INFO_URL_TEMPLATE: str = Field(...)
    CHZZK_VOD_CHAT_URL_TEMPLATE: str = Field(...)
    USER_AGENT: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )
    CHZZK_CHANNEL_VODS_URL_TEMPLATE: str = Field(...)
    CHZZK_COOKIES_FILE_PATH: str | None = Field(default=None)

    class Config:
        env_file = "chatzzk/services/collector/.env"
        env_file_encoding = "utf-8"


class CollectorSettings(BaseSettings):
    TARGET_INDEX_FOR_VIDEO_RESOLUTION: int = Field(0)

    TEMP_DIR_BASE: str = Field(default_factory=tempfile.gettempdir, description="임시 파일을 저장할 기본 디렉토리")


# 설정 객체를 싱글톤처럼 생성하여 다른 모듈에서 import하여 사용할 수 있도록 함
chzzk_api_settings = ChzzkApiSettings()
collector_settings = CollectorSettings()
