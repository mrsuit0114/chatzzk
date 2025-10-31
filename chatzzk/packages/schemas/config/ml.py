from typing import Annotated, Literal

from pydantic import BaseModel, Field

from chatzzk.packages.constants.service_codes import MAX_SPEECH_DURATION_S, MIN_SILENCE_DURATION_MS, SAMPLE_RATE


class SileroVADConfig(BaseModel):
    # 'vad_implementation'을 고정된 문자열 리터럴 타입으로 정의
    vad_implementation: Literal["silero"] = "silero"
    min_silence_duration_ms: int = Field(MIN_SILENCE_DURATION_MS)
    max_speech_duration_s: int = Field(MAX_SPEECH_DURATION_S)
    min_silence_duration_samples: int = Field(MIN_SILENCE_DURATION_MS * SAMPLE_RATE // 1000)
    threshold: float = Field(0.5)

    max_workers: int = Field(
        4
    )  # sileroVAD 모델에 의존은 아니나 cpu사용 VAD가 가능하며 다른 모델 사용 예정이 없기 때문에 여기서 정의함
    overlap_num: int = Field(3)
    sample_chunk_size: int = Field(64)


VADConfig = Annotated[SileroVADConfig, Field(discriminator="vad_implementation")]


class WhisperXConfig(BaseModel):
    asr_implementation: Literal["whisperx"] = "whisperx"
    device: str = "cuda"
    model_size: str = "large-v3"
    compute_type: str = "float16"
    batch_size: int = 4
    language: str | None = "ko"
    model_path: str = "whisperx_models"


class ASRHTTPConfig(BaseModel):
    asr_implementation: Literal["http"] = "http"
    asr_inference_server_url: str


ASRConfig = Annotated[WhisperXConfig | ASRHTTPConfig, Field(discriminator="asr_implementation")]

# UNEXPECTED_ASR_RESULTS: list[str] = ["뉴스", "고맙습니다", "감사합니다", "였습니다"]
