from loguru import logger

from chatzzk.packages.clients._http.aiohttp_client import AioHTTPClient
from chatzzk.packages.clients.ml.asr.base import ASRClientInterface
from chatzzk.packages.schemas.config.clients.ml import ASRConfig, ASRHTTPConfig, WhisperXConfig


def create_asr_client(model_config: ASRConfig, *, http_client: AioHTTPClient | None = None) -> ASRClientInterface:
    logger.info(f"Creating ASR client for implementation: {model_config.asr_implementation}")

    if isinstance(model_config, WhisperXConfig):
        from chatzzk.packages.clients.ml.asr.whisperx_client import WhisperxClient

        return WhisperxClient(config=model_config)

    elif isinstance(model_config, ASRHTTPConfig):
        if http_client is None:
            raise ValueError("http_client must be provided for ASRHTTPClient")

        from chatzzk.packages.clients.ml.asr.asr_http_client import ASRHTTPClient

        return ASRHTTPClient(config=model_config, http_client=http_client)

    else:
        raise TypeError(f"Unsupported ASR config type: {type(model_config)}")
