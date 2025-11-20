from typing import Protocol

from chatzzk_schemas.dto.api.core.vod import VODRegisterRequestDTO, VODRegisterResponseDTO


class VODDiscoveryInterface(Protocol):
    async def register_vods(self, dto: VODRegisterRequestDTO) -> list[VODRegisterResponseDTO]: ...
