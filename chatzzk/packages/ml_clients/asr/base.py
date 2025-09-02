# packages/ml_clients/asr.py (새로운 패키지)

from abc import ABC, abstractmethod

import numpy as np


# packages/ml_clients/asr/base.py
class ASRClientInterface(ABC):
    @abstractmethod
    def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        """NumPy 배열 형태의 오디오 청크를 텍스트로 변환합니다."""
        pass
