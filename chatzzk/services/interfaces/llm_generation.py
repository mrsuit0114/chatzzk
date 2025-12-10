from typing import Protocol

from chatzzk_schemas.dto.api.core.vod import (
    SummaryGenerateRequestDTO,
    SummaryGenerateResponseDTO,
    MetaSummaryGenerateRequestDTO,
    MetaSummaryGenerateResponseDTO,
)


class LLMGenerationInterface(Protocol):
    async def generate_summary(self, dto: SummaryGenerateRequestDTO) -> SummaryGenerateResponseDTO: ...

    async def generate_meta_summary(self, dto: MetaSummaryGenerateRequestDTO) -> MetaSummaryGenerateResponseDTO: ...
