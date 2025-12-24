from pydantic import BaseModel, Field

from .llm_generation import LLMGenerationConfig
from .vod_discovery import ChzzkVODDiscoveryConfig, VODDiscoveryServiceConfig


class ServicesConfig(BaseModel):
    vod_discovery: VODDiscoveryServiceConfig = Field(default_factory=VODDiscoveryServiceConfig)
    llm_generation: LLMGenerationConfig = Field(default_factory=LLMGenerationConfig)


__all__ = [
    "ServicesConfig",
    "VODDiscoveryServiceConfig",
    "ChzzkVODDiscoveryConfig",
    "LLMGenerationConfig",
]
