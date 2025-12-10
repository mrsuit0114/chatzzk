from pydantic import BaseModel, Field

from chatzzk_schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk_schemas.config.clients.http import AioHTTPConfig
from chatzzk_schemas.config.clients.media_processor import MediaProcessorConfig
from chatzzk_schemas.config.clients.ml import ASRConfig, VADConfig
from chatzzk_schemas.config.clients.llm import LangfuseConfig, LiteLLMProxyConfig


class ClientsConfig(BaseModel):
    asr: ASRConfig
    vad: VADConfig
    aiohttp: AioHTTPConfig = Field(
        default_factory=AioHTTPConfig
    )  # .env에서 주입되지않고 상수만 적용한 필드의 경우 인스턴스를 직접 생성해서 주입해야함
    chzzk_api: ChzzkAPIConfig
    media_processor: MediaProcessorConfig = Field(default_factory=MediaProcessorConfig)
    prompt_builder: LangfuseConfig
    llm_proxy: LiteLLMProxyConfig
