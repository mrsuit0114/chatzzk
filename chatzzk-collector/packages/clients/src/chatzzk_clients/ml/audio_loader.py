from torchcodec.decoders import AudioDecoder
import numpy as np
from loguru import logger
from pathlib import Path

from chatzzk_schemas.config.clients.ml import AudioLoaderConfig


class AudioLoader:
    def __init__(self, config: AudioLoaderConfig):
        self.target_sample_rate = config.target_sample_rate
        self.target_channels = config.target_channels
        self.target_dtype = config.target_dtype

    def load(self, source: Path | str) -> tuple[np.ndarray, int]:
        try:
            decoder = AudioDecoder(source, sample_rate=self.target_sample_rate, num_channels=self.target_channels)
            samples = decoder.get_all_samples()
            audio, sr = samples.data, samples.sample_rate

            audio_np = audio.numpy().squeeze().astype(self.target_dtype)

            logger.info(f"📊 Audio loaded: Duration={len(audio_np) / sr:.2f}s, Sample rate={sr}Hz")

            return audio_np, sr

        except Exception as e:
            # 입력이 무조건 Path/str이므로 별도의 타입 체크 없이 바로 str 변환 가능
            logger.error(f"❌ Failed to load audio from '{source}': {e}")
            raise
