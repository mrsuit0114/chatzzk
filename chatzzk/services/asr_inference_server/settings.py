from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from chatzzk.packages.constants.service_codes import AudioDataConstant
from chatzzk.packages.schemas.config.clients.ml import ASRConfig, WhisperXConfig


class InferenceServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="server.test.env", extra="ignore")
    asr_model_config: ASRConfig = Field(default_factory=WhisperXConfig, discriminator="asr_implementation")
    max_speech_duration_s: int = AudioDataConstant.MAX_SPEECH_DURATION_S
    target_sample_rate: int = AudioDataConstant.SAMPLE_RATE
