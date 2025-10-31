from typing import Protocol

from chatzzk.packages.schemas.dto.api.core.channel import ChannelAddRequestDTO, ChannelAddResponseDTO


# [추상화된 기능]Interface
class ChannelManagementInterface(Protocol):
    async def add_channel(self, dto: ChannelAddRequestDTO) -> ChannelAddResponseDTO: ...
