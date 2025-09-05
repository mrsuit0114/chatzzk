from pydantic import Field
from pydantic_settings import BaseSettings

from chatzzk.packages.schemas.ml_configs import ASRConfig, WhisperXConfig


class InferenceServerSettings(BaseSettings):
    models_base_dir: str | None = Field("models")
    asr_model_config: ASRConfig = Field(default_factory=WhisperXConfig)


settings = InferenceServerSettings()
