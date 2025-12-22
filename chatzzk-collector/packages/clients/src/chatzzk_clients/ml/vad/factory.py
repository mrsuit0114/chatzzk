from loguru import logger

from chatzzk_clients.ml.vad import VADClientInterface
from chatzzk_core.schemas.config.clients import SileroVADConfig, VADConfig


def create_vad_client(model_config: VADConfig) -> VADClientInterface:
    logger.info(f"Creating VAD client for implementation: {model_config.vad_implementation}")

    if isinstance(model_config, SileroVADConfig):
        from chatzzk_clients.ml.vad.silero_vad_client import SileroVADClient

        return SileroVADClient(config=model_config)
    else:
        raise TypeError(f"Unsupported VAD config type: {type(model_config)}")
