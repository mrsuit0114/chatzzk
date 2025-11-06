from dataclasses import dataclass

from chatzzk.packages.constants.service_codes import AudioDataConstant


@dataclass
class SileroVADConstant:
    VAD_IMPLEMENTATION = "silero_vad"
    MIN_SILENCE_DURATION_MS = 500
    MAX_SPEECH_DURATION_S = 30
    MIN_SILENCE_DURATION_SAMPLES = MIN_SILENCE_DURATION_MS * AudioDataConstant.SAMPLE_RATE // 1000
    THRESHOLD = 0.5
    WORKER_NUM = 4
    OVERLAP_NUM = 3
    SAMPLE_CHUNK_SIZE = 64


@dataclass
class WhisperXConstant:
    ASR_IMPLEMENTATION = "whisperx"
    DEVICE = "cuda"
    MODEL_SIZE = "large-v3"
    COMPUTE_TYPE = "float16"
    BATCH_SIZE = 4
    LANGUAGE = "ko"
    MODEL_PATH = "whisperx_models"


@dataclass
class ASRHTTPConstant:
    ASR_IMPLEMENTATION = "http"


@dataclass
class AioHTTPConstant:
    RETRY_ATTEMPTS = 3
    RETRY_WAIT_MIN_S = 1.0
    RESTRY_WAIT_MAX_S = 3.0
    TIMEOUT_S = 10.0
