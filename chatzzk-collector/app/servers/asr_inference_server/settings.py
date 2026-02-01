from pydantic import Field
from pydantic_settings import BaseSettings

from chatzzk_core.constants import AudioDataConstant
from chatzzk_core.schemas.config.clients import ASRConfig, WhisperXConfig


class InferenceServerSettings(BaseSettings):
    asr_model_config: ASRConfig = Field(default_factory=WhisperXConfig)
    max_speech_duration_s: int = AudioDataConstant.MAX_SPEECH_DURATION_S
    target_sample_rate: int = AudioDataConstant.SAMPLE_RATE
    worker_num: int = 1  # 프로세스마다 1개를 고정하고 프로세스를 여러개 띄우는 방식을 사용할 것
