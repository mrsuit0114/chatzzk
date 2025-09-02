from chatzzk.packages.ml_clients.vad.base import VADClientInterface
from chatzzk.packages.ml_clients.vad.silero_vad_client import SilieroVADClient
from chatzzk.services.vad_asr_inference_server.settings import InferenceServerSettings


def create_vad_client(settings: InferenceServerSettings) -> VADClientInterface:
    impl_name = settings.VAD_IMPLEMENTATION.upper()

    if impl_name == "SILERO":
        return SilieroVADClient(config=settings.SILERO_VAD)
    else:
        raise ValueError(f"Unknown VAD implementation: {impl_name}")
