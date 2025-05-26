# asr 모델을 load하고 오디오 입력을 받아 transcribe하는 모듈

import numpy as np
import torch
from faster_whisper import WhisperModel

# class ASR:
#     def __init__(self):
#         self.model = None
#         self.device = "cuda" if torch.cuda.is_available() else "cpu"
#         self._load_model()

#     def _load_model(self):
#         self.model = whisperx.load_model("large-v3", device=self.device, compute_type="float16")

#     def _process_audio(self, audio_data: np.ndarray):
#         if self.model is None:
#             raise ValueError("model is not loaded")
#         result = self.model.transcribe(audio_data, batch_size=4, language="ko")
#         return result["segments"][0]["text"]

#     def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
#         results = []
#         for start, end in timestamps:
#             audio_segment = audio_data[start:end]
#             results.append(self._process_audio(audio_segment))
#         return results


class ASR:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        self.model = WhisperModel("large-v3", device="cuda", compute_type="float16")

    def _process_audio(self, audio_data: np.ndarray):
        if self.model is None:
            raise ValueError("model is not loaded")
        result, _ = self.model.transcribe(audio_data, language="ko")
        return result

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
        results = []
        for start, end in timestamps:
            audio_segment = audio_data[start:end]
            result = self._process_audio(audio_segment)
            results.extend(result)
        return results
