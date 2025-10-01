import json
from datetime import datetime
from typing import Any

from loguru import logger  # Add logger for warnings in validators
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ChannelInfo(BaseModel):
    """
    치지직 채널 정보를 나타내는 Pydantic 모델.
    요청된 필드만 포함하며, snake_case와 alias를 사용합니다.
    """

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    verified_mark: bool = Field(alias="verifiedMark")
    follower_count: int = Field(alias="followerCount")
    open_live: bool = Field(alias="openLive")
    subscription_availability: bool = Field(alias="subscriptionAvailability")


class VodInfo(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    video_no: str = Field(alias="videoNo")  # 프로젝트에서 str로 다루기 때문에 매핑이 한번 필요함
    video_id: str | None = Field(default=None, alias="videoId")
    video_title: str = Field(alias="videoTitle")
    publish_date: datetime = Field(alias="publishDate")
    duration: int = Field(alias="duration")
    publish_date_at: int = Field(alias="publishDateAt")
    category_type: str = Field(alias="categoryType")
    video_category: str = Field(alias="videoCategory")
    video_category_value: str = Field(alias="videoCategoryValue")
    exposure: bool = Field(alias="exposure")
    adult: bool = Field(alias="adult")
    in_key: str | None = Field(default=None, alias="inKey")
    live_open_date: datetime | None = Field(default=None, alias="liveOpenDate")
    live_rewind_playback_json: str | None = Field(default=None, alias="liveRewindPlaybackJson")
    m3u8_url: str | None = Field(None)

    @field_validator("video_no", mode="before")
    def convert_video_no_to_str(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v)

    @model_validator(mode="after")
    def extract_m3u8_path(self) -> "VodInfo":
        if self.live_rewind_playback_json:
            try:
                parsed_json = json.loads(self.live_rewind_playback_json)
                media_list = parsed_json.get("media")
                if media_list and isinstance(media_list, list) and len(media_list) > 0:
                    first_media_item = media_list[0]
                    if isinstance(first_media_item, dict):
                        self.m3u8_url = first_media_item.get("path")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse live_rewind_playback_json for video_no={self.video_no}: {e}")
                self.m3u8_url = None
        return self


class ChannelVodsInfo(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    page: int = Field(alias="page")
    size: int = Field(alias="size")
    total_count: int = Field(alias="totalCount")
    total_pages: int = Field(alias="totalPages")
    data: list[VodInfo] = Field(alias="data")
    video_no_list: list[str] = Field([])

    @model_validator(mode="after")
    def extract_video_no_list(self) -> "ChannelVodsInfo":
        """
        self.data는 VodInfo의 리스트이므로, 각 VodInfo의 video_no를 추출하여 video_no_list에 할당합니다.
        """
        if self.data:
            # video_no는 VodInfo에서 str로 보장되므로, None 체크만 추가
            self.video_no_list = [vod.video_no for vod in self.data if vod.video_no is not None]
        return self
