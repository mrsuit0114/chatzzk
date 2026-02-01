from typing import Annotated, Literal

from pydantic import BaseModel, Field

from chatzzk_core.constants import ASRHTTPConstant, AudioDataConstant, SileroVADConstant, WhisperXConstant


class AudioLoaderConfig(BaseModel):
    target_sample_rate: int = AudioDataConstant.SAMPLE_RATE
    target_channels: int = AudioDataConstant.CHANNELS
    target_dtype: Literal[AudioDataConstant.AUDIO_DTYPE_STR] = AudioDataConstant.AUDIO_DTYPE_STR


class SileroVADConfig(BaseModel):
    implementation: Literal[SileroVADConstant.IMPLEMENTATION] = SileroVADConstant.IMPLEMENTATION
    min_silence_duration_ms: int = SileroVADConstant.MIN_SILENCE_DURATION_MS
    max_speech_duration_s: int = SileroVADConstant.MAX_SPEECH_DURATION_S
    min_silence_duration_samples: int = SileroVADConstant.MIN_SILENCE_DURATION_SAMPLES
    max_speech_duration_samples: int = SileroVADConstant.MAX_SPEECH_DURATION_SAMPLES
    threshold: float = SileroVADConstant.THRESHOLD

    worker_num: int = SileroVADConstant.WORKER_NUM
    parallel_num: int = SileroVADConstant.PARALLEL_NUM
    overlap_num: int = SileroVADConstant.OVERLAP_NUM
    sample_chunk_size: int = SileroVADConstant.SAMPLE_CHUNK_SIZE


VADConfig = Annotated[SileroVADConfig, Field(discriminator="implementation")]


class WhisperXConfig(BaseModel):
    implementation: Literal[WhisperXConstant.IMPLEMENTATION] = WhisperXConstant.IMPLEMENTATION
    device: str = WhisperXConstant.DEVICE
    model_size: str = WhisperXConstant.MODEL_SIZE
    compute_type: str = WhisperXConstant.COMPUTE_TYPE
    batch_size: int = WhisperXConstant.BATCH_SIZE
    language: str = WhisperXConstant.LANGUAGE
    model_path: str = WhisperXConstant.MODEL_PATH


class ASRHTTPConfig(BaseModel):
    implementation: Literal[ASRHTTPConstant.IMPLEMENTATION] = ASRHTTPConstant.IMPLEMENTATION
    asr_inference_server_url: str
    audio_dtype_str: Literal[AudioDataConstant.AUDIO_DTYPE_STR] = AudioDataConstant.AUDIO_DTYPE_STR


ASRConfig = Annotated[WhisperXConfig | ASRHTTPConfig, Field(discriminator="implementation")]
