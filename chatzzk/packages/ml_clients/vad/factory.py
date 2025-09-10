from loguru import logger

from chatzzk.packages.ml_clients.vad.base import VADClientInterface
from chatzzk.packages.schemas.ml_configs import SileroVADConfig, VADConfig


def create_vad_client(model_config: VADConfig, models_base_dir: str | None = None) -> VADClientInterface:
    logger.info(f"Creating VAD client for implementation: {model_config.vad_implementation}")

    if isinstance(model_config, SileroVADConfig):
        from chatzzk.packages.ml_clients.vad.silero_vad_client import SileroVADClient

        return SileroVADClient(config=model_config)
    else:
        raise TypeError(f"Unsupported ASR config type: {type(model_config)}")
