from abc import ABC, abstractmethod

import numpy as np


class VADClientInterface(ABC):
    @abstractmethod
    async def detect_speech(self, audio_chunk_np: np.ndarray) -> list[dict[str, int]]:
        """NumPy 배열 형태의 오디오 청크에서 음성 구간을 탐지합니다. start, end 타임스탬프(샘플 단위)를 반환합니다."""
        pass
