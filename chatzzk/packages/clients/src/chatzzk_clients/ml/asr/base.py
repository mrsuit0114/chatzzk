from abc import ABC, abstractmethod

import numpy as np

from chatzzk_schemas.api_models.ml import ASRResponse


class ASRClientInterface(ABC):
    @abstractmethod
    async def transcribe(self, audio_chunk_np: np.ndarray) -> ASRResponse:
        """NumPy 배열 형태의 오디오 청크를 텍스트로 변환합니다."""
        pass
