import numpy as np
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt

from chatzzk.packages.ml_clients.asr.base import ASRClientInterface
from chatzzk.packages.schemas.ml_configs import ASRHttpConfig


class ASRHttpClient(ASRClientInterface):
    def __init__(self, config: ASRHttpConfig):
        self.server_url = f"{config.asr_inference_server_url.rstrip('/')}/transcribe"
        self.session = requests.Session()
        logger.info(f"ASRHttpClient initialized for server: {self.server_url}")

    @retry(stop=stop_after_attempt(3))
    def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        try:
            files = {"audio_bytes": audio_chunk_np.astype(np.float32).tobytes()}
            data = {"dtype": "float32"}

            response = self.session.post(self.server_url, files=files, data=data, timeout=90)
            response.raise_for_status()

            return response.json().get("text", "")
        except requests.RequestException as e:
            logger.error(f"Failed to get ASR result from server: {e}")
            raise
