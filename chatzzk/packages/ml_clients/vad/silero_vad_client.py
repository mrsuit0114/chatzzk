import numpy as np
import torch
from loguru import logger
from silero_vad import get_speech_timestamps, load_silero_vad

from chatzzk.packages.ml_clients.vad.base import VADClientInterface
from chatzzk.services.vad_asr_inference_server.settings import SileroVADSettings


class SilieroVADClient(VADClientInterface):
    def __init__(self, config: SileroVADSettings):
        """
        Silero VAD 모델을 로드하고 초기화합니다.
        """
        logger.info("Initializing Silero VAD model...")
        try:
            self.model = load_silero_vad()

            self.min_silence_duration_ms = config.MIN_SILENCE_DURATION_MS
            self.max_speech_duration_s = config.MAX_SPEECH_DURATION_S

            logger.info("✅ Silero VAD model initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Silero VAD model: {e}")
            raise

    def detect_speech(self, audio_chunk_np: np.ndarray) -> list[tuple[int, int]]:
        audio_chunk_ts = torch.from_numpy(audio_chunk_np)
        results = get_speech_timestamps(
            audio_chunk_ts,
            self.model,
            min_silence_duration_ms=self.min_silence_duration_ms,
            max_speech_duration_s=self.max_speech_duration_s,
        )

        timestamps = []
        for timestamp in results:
            timestamps.append((timestamp["start"], timestamp["end"]))
        return timestamps
