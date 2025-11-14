from typing import TypeAlias

from pydantic import BaseModel

from chatzzk.packages.constants.service_codes import PlatformCode
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


class VADPerformRequestDTO(BaseModel):
    platform_code: PlatformCode
    video_no: str | int


class VADPerformResponseDTO(BaseModel):
    vad_timestamp_key: str
    vad_result: str


class ASRPerformRequestDTO(BaseModel):
    platform_code: PlatformCode
    video_no: str | int


class ASRPerformResponseDTO(BaseModel):
    asr_key: str
    asr_result: str
