from typing import Protocol

from chatzzk.packages.schemas.dto.api.core.platform import PlatformAddRequestDTO, PlatformAddResponseDTO


class PlatformManagementInterface(Protocol):
    async def add_platform(self, dto: PlatformAddRequestDTO) -> PlatformAddResponseDTO: ...
