from pydantic import BaseModel, Field

from chatzzk.packages.schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk.packages.schemas.config.clients.http import AioHTTPConfig
from chatzzk.packages.schemas.config.clients.media_processor import MediaProcessorConfig
from chatzzk.packages.schemas.config.clients.ml import ASRConfig, VADConfig


class ClientsConfig(BaseModel):
    asr: ASRConfig
    vad: VADConfig
    aiohttp: AioHTTPConfig = Field(
        default_factory=AioHTTPConfig
    )  # .env에서 주입되지않고 상수만 적용한 필드의 경우 인스턴스를 직접 생성해서 주입해야함
    chzzk_api: ChzzkAPIConfig
    media_processor: MediaProcessorConfig = Field(default_factory=MediaProcessorConfig)
