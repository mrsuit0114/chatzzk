import numpy as np
import torch
from loguru import logger
from silero_vad import get_speech_timestamps, load_silero_vad

from chatzzk.packages.ml_clients.vad.base import VADClientInterface
from chatzzk.packages.schemas.ml_configs import SileroVADConfig


class SileroVADClient(VADClientInterface):
    def __init__(self, config: SileroVADConfig):
        """
        Silero VAD 모델을 로드하고 초기화합니다.
        """
        logger.info("Initializing Silero VAD model...")
        try:
            self.model = load_silero_vad()

            self.min_silence_duration_ms = config.min_silence_duration_ms
            self.max_speech_duration_s = config.max_speech_duration_s

            logger.info("✅ Silero VAD model initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Silero VAD model: {e}")
            raise

    def detect_speech(self, audio_chunk_np: np.ndarray) -> list[tuple[int, int]]:
        audio_chunk_ts = torch.from_numpy(audio_chunk_np)
        speech_timestamps_dict = get_speech_timestamps(
            audio_chunk_ts,
            self.model,
            min_silence_duration_ms=self.min_silence_duration_ms,
            max_speech_duration_s=self.max_speech_duration_s,
        )

        return [(ts["start"], ts["end"]) for ts in speech_timestamps_dict]
