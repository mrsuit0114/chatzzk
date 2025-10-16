import asyncio
from pathlib import Path

import numpy as np
import torch
import whisperx
from loguru import logger

from chatzzk.packages.clients.ml.asr.base import AsrClientInterface
from chatzzk.packages.clients.ml.exceptions import AsrError
from chatzzk.packages.schemas.config.ml import WhisperXConfig


class WhisperxClient(AsrClientInterface):
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
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=download_root_path,
                language=self.language,
            )

            logger.info("✅ WhisperX model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WhisperX model: {e}")
            raise AsrError("Failed to initialize WhisperX model") from e

        self._lock = asyncio.Lock()

    # 비동기 병렬처리는 불가능 https://github.com/m-bain/whisperX/issues/861
    # 모델 자체에서 lock을 이용하여 동시에 모델을 접근하는 상황을 예방하고 서버 replicas를 늘려서 gpu최대로 사용하기
    def _run_transcription(self, audio_chunk_np: np.ndarray):
        result = self.model.transcribe(audio_chunk_np, batch_size=self.batch_size)
        clean_segments = [segment.get("text", "").strip() for segment in result.get("segments", [])]
        return " ".join(seg for seg in clean_segments if seg)

    async def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        async with self._lock:
            try:
                return await asyncio.to_thread(self._run_transcription, audio_chunk_np)
            except Exception as e:
                logger.error(f"WhisperX transcription failed: {e}")
                # AsrError를 발생시켜 일관된 예외 처리 보장
                raise AsrError("WhisperX transcription failed") from e
