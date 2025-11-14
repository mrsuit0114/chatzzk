from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from chatzzk.packages.constants.client import ASRHTTPConstant, SileroVADConstant, WhisperXConstant


class SileroVADConfig(BaseModel):
    vad_implementation: Literal["silero_vad"] = SileroVADConstant.VAD_IMPLEMENTATION
    min_silence_duration_ms: int = SileroVADConstant.MIN_SILENCE_DURATION_MS
    max_speech_duration_s: int = SileroVADConstant.MAX_SPEECH_DURATION_S
    min_silence_duration_samples: int = SileroVADConstant.MIN_SILENCE_DURATION_SAMPLES
    threshold: float = SileroVADConstant.THRESHOLD

    worker_num: int = SileroVADConstant.WORKER_NUM
    overlap_num: int = SileroVADConstant.OVERLAP_NUM
    sample_chunk_size: int = SileroVADConstant.SAMPLE_CHUNK_SIZE


VADConfig = Annotated[SileroVADConfig, Field(discriminator="vad_implementation")]
VADConfigAdapter = TypeAdapter(VADConfig)


def validate_vad_config(raw: dict):
    return VADConfigAdapter.validate_python(raw)


class WhisperXConfig(BaseModel):
    asr_implementation: Literal["whisperx"] = WhisperXConstant.ASR_IMPLEMENTATION
    device: str = WhisperXConstant.DEVICE
    model_size: str = WhisperXConstant.MODEL_SIZE
    compute_type: str = WhisperXConstant.COMPUTE_TYPE
    batch_size: int = WhisperXConstant.BATCH_SIZE
    language: str = WhisperXConstant.LANGUAGE
    model_path: str = WhisperXConstant.MODEL_PATH


class ASRHTTPConfig(BaseModel):
    asr_implementation: Literal["http"] = ASRHTTPConstant.ASR_IMPLEMENTATION
    asr_inference_server_url: str


ASRConfig = Annotated[WhisperXConfig | ASRHTTPConfig, Field(discriminator="asr_implementation")]
ASRConfigAdapter = TypeAdapter(ASRConfig)


def validate_asr_config(raw: dict):
    return ASRConfigAdapter.validate_python(raw)


# UNEXPECTED_ASR_RESULTS: list[str] = ["뉴스", "고맙습니다", "감사합니다", "였습니다"]
