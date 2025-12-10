from typing import TypeAlias

from pydantic import BaseModel

from chatzzk_constants.service_codes import PlatformCode
from chatzzk_schemas.dto.api.chzzk.vod import (
    ChzzkDataCollectRequestDTO,
    ChzzkDataCollectResponseDTO,
    ChzzkVODRegisterRequestDTO,
    ChzzkVODRegisterResponseDTO,
)

VODRegisterRequestDTO: TypeAlias = ChzzkVODRegisterRequestDTO
VODRegisterResponseDTO: TypeAlias = ChzzkVODRegisterResponseDTO

DataCollectRequestDTO: TypeAlias = ChzzkDataCollectRequestDTO
DataCollectResponseDTO: TypeAlias = ChzzkDataCollectResponseDTO


class _CommonRequestDTO(BaseModel):
    platform_code: PlatformCode
    video_no: str | int


class VADPerformRequestDTO(_CommonRequestDTO):
    pass


class VADPerformResponseDTO(BaseModel):
    vad_timestamp_key: str
    vad_result: str


class ASRPerformRequestDTO(_CommonRequestDTO):
    pass


class ASRPerformResponseDTO(BaseModel):
    asr_key: str
    asr_result: str


class SummaryGenerateRequestDTO(_CommonRequestDTO):
    pass


class SummaryGenerateResponseDTO(BaseModel):
    summary_raw_key: str
    summary_raw_result: str


class MetaSummaryGenerateRequestDTO(_CommonRequestDTO):
    pass


class MetaSummaryGenerateResponseDTO(BaseModel):
    meta_summary_key: str
    meta_summary_result: str
