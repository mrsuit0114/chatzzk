# m3u8을 주기적으로 확인하여 최신 오디오 segment를 가져옴
# 리샘플링(48khz -> 16khz) 수행하여 tensor로 반환

from collections import deque
from time import time
from urllib.parse import urljoin

import librosa
import m3u8
import numpy as np
import requests

# import torch


class AudioStreamProcessor:
    def __init__(self):
        self.stream_url: str
        self.vad = None
        self.asr = None
        self.fetched_segment_urls = deque(maxlen=16)
        self.np_audio_data = deque(maxlen=16)
        self.resampled_audio = None
        self.processed_audio_data = deque()  # [(ms, content)] for context

    # def load_model(self):
    # self.vad = VAD()
    # self.asr = ASR()

    # def _get_timestamps(self):
    #     return self.vad.process_audio(self.resampled_audio)

    def set_stream_url(self, stream_url: str):
        self.stream_url = stream_url

    def run(self):
        """최신 데이터 fetch and process"""
        is_updated = False
        playlist = m3u8.load(self.stream_url)
        base_url = self.stream_url.rsplit("/", 1)[0] + "/"

        for segment in playlist.segments:
            segment_url = urljoin(base_url, segment.uri)
            if segment_url in self.fetched_segment_urls:
                continue

            content = self._request_segment(segment_url)
            if content is None:  # 최신 segment라 미완성인 경우
                continue

            audio_data = np.frombuffer(content, dtype=np.int16)
            audio_data = audio_data.astype(np.float32)
            self.np_audio_data.append(audio_data)
            self.fetched_segment_urls.append(segment_url)
            is_updated = True

        if is_updated and self.np_audio_data:
            combined_audio = np.concatenate(self.np_audio_data)
            st_resampled_audio = time()
            self.resampled_audio = librosa.resample(
                combined_audio, orig_sr=48000, target_sr=16000
            )  # 16seg 1.5초 정도 걸림 -> torchaudio resample 테스트 필요
            ed_resampled_audio = time()
            print(f"resampling time: {ed_resampled_audio - st_resampled_audio}")

    def _request_segment(self, segment_url: str):
        response = requests.get(segment_url)
        if response.status_code == 200:
            content = response.content
            if len(content) % 2 != 0:
                content = content[:-1]
            return content
        else:
            return None
