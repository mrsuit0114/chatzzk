import numpy as np
import torch
from faster_whisper import WhisperModel


class ASR:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        self.model = WhisperModel("large-v3", device=self.device, compute_type="float16")

    def _process_audio(self, audio_data: np.ndarray):
        if self.model is None:
            raise ValueError("model is not loaded")
        result, _ = self.model.transcribe(audio_data, language="ko")
        text = " ".join([res.text for res in result])
        return text

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
        results = []
        for start, end in timestamps:
            audio_segment = audio_data[start:end]
            result = self._process_audio(audio_segment)
            results.extend(result)
        return results
