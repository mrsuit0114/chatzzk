# asr 모델을 load하고 오디오 입력을 받아 transcribe하는 모듈

import numpy as np
import torch

# import whisperx

TARGET_SAMPLING_RATE = 16000

# class ASR:
#     def __init__(self):
#         self.model = None
#         self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
#         self._load_model()

#     def _load_model(self):
#         self.model = whisperx.load_model("large-v3", device=self.device, compute_type="float16")

#     def _process_audio(self, audio_data: torch.Tensor):
#         audio_data_np = audio_data.numpy()
#         if self.model is None:
#             raise ValueError("model is not loaded")
#         result = self.model.transcribe(audio_data_np, batch_size=4, language="ko", beam_size=5)
#         return result["segments"]

#     def __call__(self, audio_data: torch.Tensor, timestamps: list[tuple[int, int]]):
#         results = []
#         for start, end in timestamps:
#             audio_segment = audio_data[start:end]
#             results.append(self._process_audio(audio_segment))
#         return results

from faster_whisper import WhisperModel  # noqa


class ASR:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self._load_model()

    def _load_model(self):
        self.model = WhisperModel("large-v3", device=self.device, compute_type="float16")

    def _process_audio(self, audio_data: np.ndarray):
        if self.model is None:
            raise ValueError("model is not loaded")
        results = []
        # Convert audio data to float32
        audio_data = audio_data.astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio_data, language="ko", beam_size=5)
        for segment in segments:
            results.append(segment.text)
        return results

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]):
        results = []
        for start, end in timestamps:
            audio_segment = audio_data[start:end]
            results.extend(self._process_audio(audio_segment))
        return results
