from io import BytesIO

import aiohttp
import numpy as np
from loguru import logger

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.clients.ml.asr.base import AsrClientInterface
from chatzzk.packages.clients.ml.exceptions import AsrError
from chatzzk.packages.schemas.clients.ml import AsrResponse
from chatzzk.packages.schemas.config.ml import AsrHttpConfig


class AsrHttpClient(AsrClientInterface):
    def __init__(self, config: AsrHttpConfig, http_client: BaseHttpClient):
        self.server_url = f"{config.asr_inference_server_url.rstrip('/')}/transcribe"
        self._http_client = http_client
        logger.info(f"AsrHttpClient initialized for server: {self.server_url}")

    async def transcribe(self, audio_chunk_np: np.ndarray) -> str:
        """오디오 데이터를 Asr 추론 서버로 전송하고, 변환된 텍스트를 반환합니다."""
        form_data = aiohttp.FormData()
        form_data.add_field(
            "audio_bytes",
            BytesIO(audio_chunk_np.astype(np.float32).tobytes()),
            content_type="application/octet-stream",
        )
        form_data.add_field("dtype", "float32")

        try:
            # response에 대해 점검 필요함. 아직 응답 스키마 정의 안됨
            response = await self._http_client.post(self.server_url, data=form_data, timeout=90)
            validated_response = AsrResponse.model_validate(response)
            return validated_response.text
        except aiohttp.ClientError as e:
            logger.error(f"Asr server request failed: {e}")
            raise AsrError("Asr inference server request failed") from e
        except Exception as e:
            logger.exception("An unexpected error occurred during Asr transcription")
            raise AsrError("An unexpected error occurred during transcription") from e
