from pathlib import Path

from loguru import logger

from chatzzk.packages.clients._http.client import BaseHTTPClient
from chatzzk.packages.clients.ml.asr.base import ASRClientInterface
from chatzzk.packages.schemas.config.ml import ASRConfig, ASRHTTPConfig, WhisperXConfig


def create_asr_client(
    model_config: ASRConfig, *, http_client: BaseHTTPClient | None = None, models_base_dir: str | None = None
) -> ASRClientInterface:
    logger.info(f"Creating ASR client for implementation: {model_config.asr_implementation}")

    if isinstance(model_config, WhisperXConfig):
        from chatzzk.packages.clients.ml.asr.whisperx_client import WhisperxClient

        final_model_path = model_config.model_path
        if models_base_dir:
            final_model_path = str(Path(models_base_dir) / model_config.model_path)

        return WhisperxClient(config=model_config, model_path=final_model_path)

    elif isinstance(model_config, ASRHTTPConfig):
        if http_client is None:
            raise ValueError("http_client must be provided for ASRHTTPClient")

        from chatzzk.packages.clients.ml.asr.asr_http_client import ASRHTTPClient

        return ASRHTTPClient(config=model_config, http_client=http_client)

    else:
        raise TypeError(f"Unsupported ASR config type: {type(model_config)}")
