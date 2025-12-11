from io import BytesIO

import aiohttp
import numpy as np
from loguru import logger

from chatzzk_clients._http.aiohttp_client import AioHTTPClient
from chatzzk_clients.ml.asr.base import ASRClientInterface
from chatzzk_clients.ml.exceptions import ASRError
from chatzzk_schemas.external.ml import ASRResponse
from chatzzk_schemas.config.clients.ml import ASRHTTPConfig


class ASRHTTPClient(ASRClientInterface):
    def __init__(self, config: ASRHTTPConfig, http_client: AioHTTPClient):
        self.server_url = f"{config.asr_inference_server_url.rstrip('/')}/transcribe"
        self._http_client = http_client
        logger.info(f"ASRHTTPClient initialized for server: {self.server_url}")

    async def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        """오디오 데이터를 ASR 추론 서버로 전송하고, 변환된 텍스트를 반환합니다."""
        form_data = aiohttp.FormData()
        form_data.add_field(
            "audio_bytes",
            BytesIO(audio_chunk_np.astype(np.float32).tobytes()),
            content_type="application/octet-stream",
        )
        form_data.add_field("dtype", "float32")

        try:
            async with self._http_client.post(self.server_url, data=form_data) as response:
                data = await response.json()
                validated_response = ASRResponse.model_validate(data)

            return validated_response.text
        except aiohttp.ClientError as e:
            logger.error(f"ASR server request failed: {e}")
            raise ASRError("ASR inference server request failed") from e
        except Exception as e:
            logger.exception("An unexpected error occurred during ASR transcription")
            raise ASRError("An unexpected error occurred during transcription") from e
