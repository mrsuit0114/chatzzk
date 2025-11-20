from typing import Protocol

from chatzzk_schemas.dto.api.core.vod import DataCollectRequestDTO, DataCollectResponseDTO


class DataCollectionInterface(Protocol):
    async def collect_data(self, dto: DataCollectRequestDTO) -> DataCollectResponseDTO: ...
