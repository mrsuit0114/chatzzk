from pathlib import Path

import numpy as np
from loguru import logger
from torchcodec.decoders import AudioDecoder

from chatzzk_core.schemas.config.clients import AudioLoaderConfig


class AudioLoader:
    def __init__(self, config: AudioLoaderConfig):
        self.target_sample_rate = config.target_sample_rate
        self.target_channels = config.target_channels
        self.target_dtype = config.target_dtype

    def load(self, source: Path | str) -> tuple[np.ndarray, int]:
        try:
            decoder = self.get_decoder(source)
            samples = decoder.get_all_samples()

            audio_np = self.to_numpy(samples)

            logger.info(
                f"📊 Audio loaded: Duration={len(audio_np) / self.target_sample_rate:.2f}s, Sample rate={self.target_sample_rate}Hz"
            )

            return audio_np, self.target_sample_rate

        except Exception as e:
            # 입력이 무조건 Path/str이므로 별도의 타입 체크 없이 바로 str 변환 가능
            logger.error(f"❌ Failed to load audio from '{source}': {e}")
            raise

    def get_decoder(self, source: Path | str) -> AudioDecoder:
        try:
            # sample_rate와 num_channels를 지정하면 디코딩 시 자동 변환됨
            return AudioDecoder(source, sample_rate=self.target_sample_rate, num_channels=self.target_channels)
        except Exception as e:
            logger.error(f"❌ Failed to create AudioDecoder for '{source}': {e}")
            raise

    def to_numpy(self, audio_samples) -> np.ndarray:
        return audio_samples.data.numpy().squeeze().astype(self.target_dtype)
