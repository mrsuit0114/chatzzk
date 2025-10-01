import asyncio
from pathlib import Path

import numpy as np
import torch
import whisperx
from loguru import logger

from chatzzk.packages.clients.ml.asr.base import ASRClientInterface
from chatzzk.packages.clients.ml.exceptions import ASRError
from chatzzk.packages.schemas.config.ml import WhisperXConfig


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
            raise ASRError("Failed to initialize WhisperX model") from e

    # 추론 서버 워커는 gpu 1개마다 띄운다 했을 때 동시에 처리할 작업수를 5개정도로 제한하면 되려나? 서버에서 추론하는 부분에 asyncio 세마포어 적용
    async def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        def _run_transcription():
            """WhisperX의 동기적인 transcribe 함수를 실행하는 래퍼 함수"""
            try:
                result = self.model.transcribe(audio_chunk_np, batch_size=self.batch_size, language=self.language)
                clean_segments = [segment.get("text", "").strip() for segment in result.get("segments", [])]
                return " ".join(seg for seg in clean_segments if seg)
            except Exception as e:
                logger.error(f"WhisperX transcription failed: {e}")
                # ASRError를 발생시켜 일관된 예외 처리 보장
                raise ASRError("WhisperX transcription failed") from e

        # 동기 함수를 별도의 스레드에서 실행하여 이벤트 루프를 막지 않음
        return await asyncio.to_thread(_run_transcription)
