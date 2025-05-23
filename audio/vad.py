# 오디오 입력(30초)을 받아 vad구간을 반환함
# 이미 처리된 구간에 대해서는 처리하지 않도록 샘플의 시작위치를 조정
# 마지막(현재 말하고 있음)구간도 반환해야함
# vad가 파일 말고 메모리에 있는 오디오 데이터에 대해 수행할 수 있도록 수정

import numpy as np
import torch
from silero_vad import get_speech_timestamps, load_silero_vad


class VAD:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        self.model = load_silero_vad()

    def __call__(self, audio_data: np.ndarray | torch.Tensor):
        audio_data = torch.from_numpy(audio_data).float() / 32768.0
        timestamps = get_speech_timestamps(audio_data, self.model)
        results = []
        for timestamp in timestamps:
            results.append((timestamp["start"], timestamp["end"]))
        return results
