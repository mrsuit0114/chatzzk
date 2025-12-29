from datetime import datetime

from pydantic import BaseModel, ConfigDict

from chatzzk_core.constants import PlatformCode, VODPipelineStatus


class PlatformDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    platform_code: PlatformCode
    platform_url: str


class ChannelDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    platform_id: int
    platform_channel_id: str
    channel_name: str
    last_vod_crawled_at: datetime | None
    is_collection_enabled: bool
    vod_exposure_delay_hours: int


class VODDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    channel_id: int
    video_no: str
    video_title: str
    pipeline_status: VODPipelineStatus
    duration: int
    publish_date: datetime


class TargetVODInfo(BaseModel):
    vod: VODDTO
    channel: ChannelDTO
    platform: PlatformDTO
