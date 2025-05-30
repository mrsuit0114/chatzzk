import numpy as np
import torch
import whisperx
from loguru import logger


class ASR:
    COMPUTE_TYPE = "float16"
    BATCH_SIZE = 4

    def __init__(self, model_size: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self._load_model(model_size)

    def _load_model(self, model_size: str):
        model = whisperx.load_model(model_size, device=self.device, compute_type=self.COMPUTE_TYPE)
        if model is None:
            logger.error("Failed to load whisperx model")
            raise ValueError("Failed to load whisperx model")
        logger.info("WhisperX model loaded successfully")
        return model

    def _process_audio(self, audio_data: np.ndarray) -> str:
        """
        Transcribe a segment of audio data into text.

        Args:
            audio_data (np.ndarray): A numpy array containing audio waveform data.

        Returns:
            str: The transcribed text from the audio segment.
        """
        result = self.model.transcribe(audio_data, batch_size=self.BATCH_SIZE, language="ko")
        text = "".join([res["text"] for res in result["segments"]])
        return text

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]) -> list[str]:
        results = []
        for start, end in timestamps:
            audio_segment = audio_data[start:end]
            results.append(self._process_audio(audio_segment))
        return results
