from pydantic import BaseModel, Field

from .vod_discovery import ChzzkVODDiscoveryConfig, VODDiscoveryServiceConfig


class ServicesConfig(BaseModel):
    vod_discovery: VODDiscoveryServiceConfig = Field(default_factory=VODDiscoveryServiceConfig)


__all__ = [
    "ServicesConfig",
    "VODDiscoveryServiceConfig",
    "ChzzkVODDiscoveryConfig",
]
