from typing import Annotated, Literal

from pydantic import BaseModel, Field

from chatzzk.packages.constants.service_codes import MAX_SPEECH_DURAION_S


class SileroVADConfig(BaseModel):
    # 'vad_implementation'을 고정된 문자열 리터럴 타입으로 정의
    vad_implementation: Literal["silero"] = "silero"
    min_silence_duration_ms: int = 500
    max_speech_duration_s: int = Field(MAX_SPEECH_DURAION_S)


VADConfig = Annotated[SileroVADConfig, Field(discriminator="vad_implementation")]


class WhisperXConfig(BaseModel):
    asr_implementation: Literal["whisperx"] = "whisperx"
    device: str = "cuda"
    model_size: str = "large-v3"
    compute_type: str = "float16"
    batch_size: int = 4
    language: str | None = "ko"
    model_path: str = "whisperx_models"


class ASRHttpConfig(BaseModel):
    asr_implementation: Literal["http"] = "http"
    asr_inference_server_url: str


ASRConfig = Annotated[WhisperXConfig | ASRHttpConfig, Field(discriminator="asr_implementation")]

# UNEXPECTED_ASR_RESULTS: list[str] = ["뉴스", "고맙습니다", "감사합니다", "였습니다"]
