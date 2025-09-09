from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.constants.service_codes import MAX_SPEECH_DURAION_S, SAMPLE_RATE
from chatzzk.packages.schemas.ml_configs import ASRConfig, WhisperXConfig


class InferenceServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    models_base_dir: str | None = Field("/app/models")
    asr_model_config: ASRConfig = Field(default_factory=WhisperXConfig)
    max_speech_duration_s: int = Field(MAX_SPEECH_DURAION_S)
    sample_rate: int = Field(SAMPLE_RATE)


settings = InferenceServerSettings()
