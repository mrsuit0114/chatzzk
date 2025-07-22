import numpy as np
import torch
import whisperx
from loguru import logger


class ASR:
    COMPUTE_TYPE = "float16"
    BATCH_SIZE = 4

    def __init__(self, model_size: str, not_expected_asr_list: list[str]):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"  # cpu 사용 시 서비스 불가 - 에러처리
        self.model = self._load_model(model_size)
        self.not_expected_asr_list = not_expected_asr_list
        if self.device == "cpu":
            logger.error("ASR doesn't work well with cpu!!")

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
        text = "".join([res["text"] for res in result["segments"]]).strip()
        return text

    def _is_not_expected_asr(self, text: str) -> bool:
        if any(not_expected_asr in text for not_expected_asr in self.not_expected_asr_list):
            return True
        return False

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]) -> list[str]:
        results = []
        for start, end in timestamps:
            audio_segment = audio_data[start:end]
            processed_asr = self._process_audio(audio_segment)
            if self._is_not_expected_asr(processed_asr):
                continue
            results.append(processed_asr)
        return results
