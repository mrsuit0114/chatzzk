from loguru import logger

from chatzzk.packages.clients.ml.vad.base import VadClientInterface
from chatzzk.packages.schemas.config.ml import SileroVadConfig, VadConfig


def create_vad_client(model_config: VadConfig, *, models_base_dir: str | None = None) -> VadClientInterface:
    logger.info(f"Creating Vad client for implementation: {model_config.vad_implementation}")

    if isinstance(model_config, SileroVadConfig):
        from chatzzk.packages.clients.ml.vad.silero_vad_client import SileroVadClient

        return SileroVadClient(config=model_config)
    else:
        raise TypeError(f"Unsupported Vad config type: {type(model_config)}")
