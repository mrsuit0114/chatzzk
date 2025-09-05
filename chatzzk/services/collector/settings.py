import tempfile

from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.schemas.ml_configs import ASRConfig, ASRHttpConfig, SileroVADConfig, VADConfig


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
    asr_model_config: ASRConfig = Field(default_factory=ASRHttpConfig)
    # asr_model_config: ASRConfig = ASRHttpConfig(asr_inference_server_url=asr_inference_server_url)  # 인스턴스를 생성하기 전이기 때문에 asr.. 변수가 존재하지 않는 시점

    @model_validator(mode="before")
    @classmethod
    def assemble_asr_config(cls, values: dict) -> dict:
        """
        주어진 환경 변수 값을 기반으로 ASR_CONFIG를 동적으로 생성합니다.
        'before' 모드를 사용하여, Pydantic이 ASR_CONFIG를 파싱하기 전에
        미리 올바른 딕셔너리를 만들어 넣어줍니다.
        """
        asr_inference_server_url = values.get("asr_inference_server_url")

        if asr_inference_server_url:
            # URL이 있으면, 'http' 구현을 사용하도록 딕셔셔너리 구성
            logger.info("ASR_INFERENCE_SERVER_URL found. Configuring for REMOTE execution.")
            values["asr_model_config"] = {
                "asr_implementation": "http",
                "asr_inference_server_url": asr_inference_server_url,
            }
        else:
            # URL이 없으면, 'whisperx' 구현을 사용하도록 딕셔셔너리 구성
            logger.info("ASR_INFERENCE_SERVER_URL not found. Configuring for LOCAL execution.")
            values["asr_model_config"] = {
                "asr_implementation": "whisperx",
                # .env에서 COLLECTOR_WHISPERX__MODEL_PATH_OR_NAME 등으로
                # 기본값을 덮어쓸 수도 있음
                **values.get("WHISPERX", {}),
            }

        return values


# 설정 객체를 싱글톤처럼 생성하여 다른 모듈에서 import하여 사용할 수 있도록 함
chzzk_api_settings = ChzzkApiSettings()
collector_settings = CollectorSettings()
