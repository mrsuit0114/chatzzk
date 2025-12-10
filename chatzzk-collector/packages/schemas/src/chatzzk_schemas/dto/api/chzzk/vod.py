from datetime import datetime

from pydantic import BaseModel


class ChzzkVODRegisterRequestDTO(BaseModel):
    platform_channel_id: str
    collect_after_date_utc: datetime


class ChzzkVODRegisterResponseDTO(BaseModel):
    video_no: int
    status: str


class ChzzkDataCollectRequestDTO(BaseModel):
    video_no: int


class ChzzkDataCollectResponseDTO(BaseModel):
    video_no: int
    chat_result: str
    audio_result: str
