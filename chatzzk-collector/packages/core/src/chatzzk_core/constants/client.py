from dataclasses import dataclass

from chatzzk_core.constants.service_codes import AudioDataConstant, MLModelPath


@dataclass
class SileroVADConstant:
    VAD_IMPLEMENTATION = "silero_vad"
    MIN_SILENCE_DURATION_MS = 500
    MAX_SPEECH_DURATION_S = AudioDataConstant.MAX_SPEECH_DURATION_S
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
    MODEL_PATH = MLModelPath.WHISPERX


@dataclass
class ASRHTTPConstant:
    ASR_IMPLEMENTATION = "http"


@dataclass
class AioHTTPConstant:
    RETRY_ATTEMPTS = 5
    RETRY_WAIT_MIN_S = 4.0
    RETRY_WAIT_MAX_S = 10.0
    MULTIPLIER = 1
    TIMEOUT_S = 10.0


@dataclass
class MediaProcessorConstant:
    TARGET_SAMPLE_RATE = AudioDataConstant.SAMPLE_RATE
    TARGET_CHANNELS = AudioDataConstant.CHANNELS
    ACODEC = AudioDataConstant.ACODEC
    WORKER_NUM = 16
    CHUNK_SIZE = 8192
