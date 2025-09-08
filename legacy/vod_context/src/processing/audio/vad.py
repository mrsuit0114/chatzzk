import numpy as np
import torch
from loguru import logger
from silero_vad import get_speech_timestamps, load_silero_vad

from config import Config


class VAD:
    def __init__(self, config: Config):
        self.model = self._load_model()
        self.min_silence_duration_ms = config.VAD.MIN_SILENCE_DURATION_MS
        self.max_speech_duration_s = config.VAD.MAX_SPEECH_DURATION_S

    def _load_model(self):
        model = load_silero_vad()
        if model is None:
            logger.error("Failed to load silero_vad model")
            raise ValueError("Failed to load silero_vad model")
        logger.info("Silero VAD model loaded successfully")
        return model

    def __call__(self, audio_data: np.ndarray) -> list[tuple[int, int]]:
        audio_data = torch.from_numpy(audio_data)
        timestamps = get_speech_timestamps(
            audio_data,
            self.model,
            min_silence_duration_ms=self.min_silence_duration_ms,
            max_speech_duration_s=self.max_speech_duration_s,
        )
        results = []
        for timestamp in timestamps:
            results.append((timestamp["start"], timestamp["end"]))
        return results
