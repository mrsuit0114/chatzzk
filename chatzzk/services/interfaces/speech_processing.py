from typing import Protocol

from chatzzk_schemas.dto.api.core.vod import (
    ASRPerformRequestDTO,
    ASRPerformResponseDTO,
    VADPerformRequestDTO,
    VADPerformResponseDTO,
)


# [추상화된 기능]Interface
class SpeechProcessingInterface(Protocol):
    async def perform_vad(self, dto: VADPerformRequestDTO) -> VADPerformResponseDTO: ...

    async def perform_asr(self, dto: ASRPerformRequestDTO) -> ASRPerformResponseDTO: ...
