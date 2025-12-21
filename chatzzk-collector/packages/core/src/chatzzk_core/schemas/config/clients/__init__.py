from pydantic import BaseModel, Field

from .chzzk import ChzzkAPIConfig
from .http import AioHTTPConfig
from .llm import LangfuseConfig, LiteLLMProxyConfig
from .media_processor import MediaProcessorConfig
from .ml import ASRConfig, AudioLoaderConfig, VADConfig


class ClientsConfig(BaseModel):
    audio_loader: AudioLoaderConfig = Field(default_factory=AudioLoaderConfig)
    asr: ASRConfig
    vad: VADConfig
    aiohttp: AioHTTPConfig = Field(
        default_factory=AioHTTPConfig
    )  # .env에서 주입되지않고 상수만 적용한 필드의 경우 인스턴스를 직접 생성해서 주입해야함
    chzzk_api: ChzzkAPIConfig
    media_processor: MediaProcessorConfig = Field(default_factory=MediaProcessorConfig)
    prompt_builder: LangfuseConfig
    llm_proxy: LiteLLMProxyConfig


__all__ = [
    "ClientsConfig",
    "AudioLoaderConfig",
    "ASRConfig",
    "VADConfig",
    "AioHTTPConfig",
    "ChzzkAPIConfig",
    "MediaProcessorConfig",
    "LangfuseConfig",
    "LiteLLMProxyConfig",
]
