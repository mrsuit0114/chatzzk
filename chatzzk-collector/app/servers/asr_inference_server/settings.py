from pydantic import Field
from pydantic_settings import BaseSettings

from chatzzk_core.constants.service_codes import AudioDataConstant
from chatzzk_core.schemas.config.clients.ml import ASRConfig, WhisperXConfig


class InferenceServerSettings(BaseSettings):
    asr_model_config: ASRConfig = Field(default_factory=WhisperXConfig)
    max_speech_duration_s: int = AudioDataConstant.MAX_SPEECH_DURATION_S
    target_sample_rate: int = AudioDataConstant.SAMPLE_RATE
