from pathlib import Path

import numpy as np
import torch
import whisperx
from loguru import logger

from chatzzk.packages.ml_clients.asr.base import ASRClientInterface
from chatzzk.services.vad_asr_inference_server.settings import WhisperXSettings


class WhisperxClient(ASRClientInterface):
    def __init__(self, config: WhisperXSettings, model_path: str | Path):
        logger.info("Initializing WhisperX model...")
        try:
            self.device = config.DEVICE if torch.cuda.is_available() else "cpu"
            self.model_size = config.MODEL_SIZE
            self.compute_type = config.COMPUTE_TYPE
            self.batch_size = config.BATCH_SIZE
            self.language = config.LANGUAGE
            self.model = whisperx.load_model(
                self.model_size, device=self.device, compute_type=self.compute_type, download_root=Path(model_path)
            )

            logger.info("✅ WhisperX model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WhisperX model: {e}")
            raise

    def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        try:
            result = self.model.transcribe(audio_chunk_np, batch_size=self.batch_size, language=self.language)

            text_segments = []

            for segment in result["segments"]:
                segment_text = segment.get("text", "")
                text_segments.append(segment_text)

            return "".join(text_segments).strip()
        except Exception as e:
            logger.error(f"WhisperX transcription failed: {e}")
            return ""
