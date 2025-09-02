from pathlib import Path

from chatzzk.packages.ml_clients.asr.base import ASRClientInterface
from chatzzk.packages.ml_clients.asr.whisperx_client import WhisperxClient
from chatzzk.services.vad_asr_inference_server.settings import InferenceServerSettings


def create_asr_client(settings: InferenceServerSettings) -> ASRClientInterface:
    impl_name = settings.ASR_IMPLEMENTATION.upper()

    if impl_name == "WHISPERX":
        whisperx_config = settings.WHISPERX

        if settings.MODELS_BASE_DIR:
            model_path = str(Path(settings.MODELS_BASE_DIR) / whisperx_config.MODEL_PATH)
        else:
            model_path = None

        return WhisperxClient(config=settings.WHISPERX, model_path=model_path)

    else:
        raise ValueError(f"Unknown ASR implementation: {impl_name}")
