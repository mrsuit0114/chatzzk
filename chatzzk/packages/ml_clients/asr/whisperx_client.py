from pathlib import Path

import numpy as np
import torch
import whisperx
from loguru import logger

from chatzzk.packages.ml_clients.asr.base import ASRClientInterface
from chatzzk.packages.schemas.ml_configs import WhisperXConfig


class WhisperxClient(ASRClientInterface):
    def __init__(self, config: WhisperXConfig, model_path: str | Path | None):
        logger.info("Initializing WhisperX model...")
        self.device = config.device if torch.cuda.is_available() else "cpu"
        self.model_size = config.model_size
        self.compute_type = config.compute_type
        self.batch_size = config.batch_size
        self.language = config.language
        logger.info(f"Initializing WhisperX model '{self.model_size}' on device '{self.device}'...")

        download_root_path = Path(model_path) if model_path else None
        try:
            self.model = whisperx.load_model(
                self.model_size, device=self.device, compute_type=self.compute_type, download_root=download_root_path
            )

            logger.info("✅ WhisperX model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WhisperX model: {e}")
            raise

    def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        try:
            result = self.model.transcribe(audio_chunk_np, batch_size=self.batch_size, language=self.language)

            clean_segments = [segment.get("text", "").strip() for segment in result.get("segments", [])]

            return " ".join(seg for seg in clean_segments if seg)
        except Exception as e:
            logger.error(f"WhisperX transcription failed: {e}")
            raise
