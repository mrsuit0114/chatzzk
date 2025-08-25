# packages/ml_clients/asr.py (새로운 패키지)

from abc import ABC, abstractmethod

import numpy as np
from packages.schemas.asr import ASRResponse  # 기존 스키마 재활용


class ASRClientInterface(ABC):
    """
    ASR 추론 클라이언트에 대한 추상 인터페이스.
    모든 ASR 클라이언트는 이 클래스를 상속받아 구현해야 합니다.
    """

    @abstractmethod
    def transcribe(self, audio_array: np.ndarray, language: str) -> ASRResponse:
        """
        오디오 배열을 받아 텍스트로 변환합니다.
        """
        pass
