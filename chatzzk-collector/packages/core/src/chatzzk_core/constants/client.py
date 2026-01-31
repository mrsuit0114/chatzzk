from .service_code import AudioDataConstant, MLModelPaths


class SileroVADConstant:
    IMPLEMENTATION = "silero_vad"
    MIN_SILENCE_DURATION_MS = AudioDataConstant.MIN_SILENCE_DURATION_MS
    MAX_SPEECH_DURATION_S = AudioDataConstant.MAX_SPEECH_DURATION_S
    MIN_SILENCE_DURATION_SAMPLES = MIN_SILENCE_DURATION_MS * AudioDataConstant.SAMPLE_RATE // 1000
    MAX_SPEECH_DURATION_SAMPLES = MAX_SPEECH_DURATION_S * AudioDataConstant.SAMPLE_RATE
    THRESHOLD = 0.5
    PARALLEL_NUM = 2  # 일단은 asr 동시성과 동일하게 설정함 - 병목 지점인 asr이 개선되기전까지는 수정에 큰 의미가 없음
    WORKER_NUM = 4
    OVERLAP_NUM = 3
    SAMPLE_CHUNK_SIZE = 64


class WhisperXConstant:
    IMPLEMENTATION = "whisperx"
    DEVICE = "cuda"
    MODEL_SIZE = "large-v3"
    COMPUTE_TYPE = "float16"
    BATCH_SIZE = 4
    LANGUAGE = "ko"
    MODEL_PATH = MLModelPaths.WHISPERX


class ASRHTTPConstant:
    IMPLEMENTATION = "http"


class AioHTTPConstant:
    RETRY_ATTEMPTS = 5
    RETRY_WAIT_MIN_S = 4.0
    RETRY_WAIT_MAX_S = 10.0
    MULTIPLIER = 1
    TIMEOUT_S = 10.0


class MediaProcessorConstant:
    TARGET_SAMPLE_RATE = AudioDataConstant.SAMPLE_RATE
    TARGET_CHANNELS = AudioDataConstant.CHANNELS
    ACODEC = AudioDataConstant.ACODEC
    WORKER_NUM = 16
    CHUNK_SIZE = 8192
