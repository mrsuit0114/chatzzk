from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class ASRClientInterface(ABC):
    @abstractmethod
    async def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        """NumPy 배열 형태의 오디오 청크를 텍스트로 변환합니다."""
        pass
