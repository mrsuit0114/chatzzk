from pydantic import BaseModel, Field

from .chzzk import ChzzkAPIConfig
from .http import AioHTTPConfig
from .llm import ContextAssemblerConfig, LangfuseConfig, LiteLLMConfig
from .media_processor import MediaProcessorConfig
from .ml import ASRConfig, ASRHTTPConfig, AudioLoaderConfig, SileroVADConfig, VADConfig, WhisperXConfig


class ClientsConfig(BaseModel):
    audio_loader: AudioLoaderConfig = Field(default_factory=AudioLoaderConfig)
    asr: ASRConfig
    vad: VADConfig
    aiohttp: AioHTTPConfig = Field(
        default_factory=AioHTTPConfig
    )  # .env에서 주입되지않고 상수만 적용한 필드의 경우 인스턴스를 직접 생성해서 주입해야함
    chzzk_api: ChzzkAPIConfig
    media_processor: MediaProcessorConfig = Field(default_factory=MediaProcessorConfig)
    prompt_manager: LangfuseConfig
    llm_client: LiteLLMConfig
    context_assembler: ContextAssemblerConfig = Field(default_factory=ContextAssemblerConfig)


__all__ = [
    "ClientsConfig",
    "AudioLoaderConfig",
    "ASRConfig",
    "VADConfig",
    "AioHTTPConfig",
    "ChzzkAPIConfig",
    "MediaProcessorConfig",
    "LangfuseConfig",
    "ContextAssemblerConfig",
    "LiteLLMConfig",
    "ASRHTTPConfig",
    "SileroVADConfig",
    "WhisperXConfig",
]
