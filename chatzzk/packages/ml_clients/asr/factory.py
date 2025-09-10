from pathlib import Path

from loguru import logger

from chatzzk.packages.ml_clients.asr.base import ASRClientInterface
from chatzzk.packages.schemas.ml_configs import ASRConfig, ASRHttpConfig, WhisperXConfig


def create_asr_client(model_config: ASRConfig, models_base_dir: str | None = None) -> ASRClientInterface:
    logger.info(f"Creating ASR client for implementation: {model_config.asr_implementation}")

    # Pydantic이 이미 올바른 타입으로 파싱해줬으므로,
    # 우리는 그 타입을 확인하기만 하면 됨
    if isinstance(model_config, WhisperXConfig):
        from chatzzk.packages.ml_clients.asr.whisperx_client import WhisperxClient

        final_model_path = model_config.model_path
        if models_base_dir:
            final_model_path = str(Path(models_base_dir) / model_config.model_path)
        else:
            final_model_path = None

        return WhisperxClient(config=model_config, model_path=final_model_path)

    elif isinstance(model_config, ASRHttpConfig):
        from chatzzk.packages.ml_clients.asr.asr_http_client import ASRHttpClient

        return ASRHttpClient(config=model_config)

    else:
        raise TypeError(f"Unsupported ASR config type: {type(model_config)}")
