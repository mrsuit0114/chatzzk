import numpy as np
import torch
from loguru import logger
from silero_vad import get_speech_timestamps, load_silero_vad


class VAD:
    """Voice Activity Detection (VAD) class that identifies speech segments in audio data.

    This class uses the Silero VAD model to detect speech segments in audio data and returns
    their timestamps. The model can be run on CPU or GPU, though CPU performance is currently
    sufficient for most use cases.
    """

    def __init__(self, min_silence_duration_ms: int, max_speech_duration_s: int):
        self.model = self._load_model()
        self.min_silence_duration_ms = min_silence_duration_ms
        self.max_speech_duration_s = max_speech_duration_s

    def _load_model(self):
        model = load_silero_vad()
        if model is None:
            logger.error("Failed to load silero_vad model")
            raise ValueError("Failed to load silero_vad model")
        logger.info("Silero VAD model loaded successfully")
        return model

    def __call__(self, audio_data: np.ndarray) -> list[tuple[int, int]]:
        """Detect speech segments in audio data and return their timestamps.

        Args:
            audio_data (np.ndarray): Input audio data as a numpy array float32 normalized to -1.0 to 1.0

        Returns:
            list[tuple[int, int]]: List of tuples containing start and end timestamps
                for each detected speech segment.

        Note:
            - min_silence_duration_ms: Minimum duration of silence (in milliseconds) required
                to split speech segments. Segments separated by silence shorter than this
                will be merged into a single segment.
            - max_speech_duration_s: Maximum allowed duration (in seconds) for a single
                speech segment. Longer segments will be split at this boundary.
        """
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
