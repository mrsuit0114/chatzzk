from typing import TypeAlias

from chatzzk.packages.schemas.dto.api.chzzk.vod import (
    ChzzkDataCollectRequestDTO,
    ChzzkDataCollectResponseDTO,
    ChzzkVODRegisterRequestDTO,
    ChzzkVODRegisterResponseDTO,
)

VODRegisterRequestDTO: TypeAlias = ChzzkVODRegisterRequestDTO
VODRegisterResponseDTO: TypeAlias = ChzzkVODRegisterResponseDTO

DataCollectRequestDTO: TypeAlias = ChzzkDataCollectRequestDTO
DataCollectResponseDTO: TypeAlias = ChzzkDataCollectResponseDTO
