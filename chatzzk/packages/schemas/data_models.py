from typing import Any

import orjson
from pydantic import BaseModel, ConfigDict, Field, field_validator

from chatzzk.packages.constants.service_codes import ContextType


class StreamContextEntry(BaseModel):
    timestamp_ms: int
    type: ContextType
    content: str
    pay_amount: int


class VideoSummary(BaseModel):
    start_ms: int
    end_ms: int
    content: str


class ChzzkVodInfo(BaseModel):
    # Python 코드에서는 snake_case (video_no) 사용
    video_no: str = Field(..., alias="videoNo")  # ⭐ JSON의 'videoNo' 키를 이 필드에 매핑
    video_title: str = Field(..., alias="videoTitle")
    duration: int
    video_category_value: str = Field(..., alias="videoCategoryValue")
    channel_id: str = Field(..., alias="channel")
    live_open_date: str = Field(..., alias="liveOpenDate")
    publish_date: str = Field(..., alias="publishDate")

    @field_validator("video_no", mode="before")
    @classmethod
    def validate_video_no_to_str(cls, v: int) -> str:
        return str(v)

    @field_validator("channel_id", mode="before")
    @classmethod
    def flatten_channel_id(cls, values: dict) -> str:
        channel_id = values.get("channelId")
        if channel_id:
            return channel_id
        raise ValueError("Could not find 'channelId' in 'channel' object")

    model_config = ConfigDict(populate_by_name=True)


class VideoEntry(BaseModel):
    videoNo: int


# 전체 API 응답을 나타내는 모델
class ChannelVodsResponse(BaseModel):
    data: list[VideoEntry] = Field(default_factory=list)


class Extras(BaseModel):
    pay_amount: int = Field(0, alias="payAmount")


class ChatEntry(BaseModel):
    message_type_code: int = Field(..., alias="messageTypeCode")
    player_message_time: int = Field(..., alias="playerMessageTime")
    content: str
    extras: Extras | None = Field(None)

    @field_validator("extras", mode="before")
    @classmethod
    def parse_extras_json(cls, value: Any):
        # 이미 dict면 그대로 반환
        if isinstance(value, dict):
            return value
        # 문자열이면 orjson으로 파싱
        if isinstance(value, str):
            try:
                return orjson.loads(value)
            except Exception as e:
                raise ValueError("extras 필드 JSON 파싱 실패") from e
        # None 등은 그대로 처리
        return value


# ChatApiResponse 모델: 전체 API 응답을 표현
class ChatApiResponse(BaseModel):
    video_chats: list[ChatEntry] | None = Field(default_factory=list, alias="videoChats")
    next_player_message_time: int | None = Field(None, alias="nextPlayerMessageTime")


class ChzzkChannelInfo(BaseModel):
    channel_id: str = Field(..., alias="channelId")
    channel_name: str = Field(..., alias="channelName")
    verified_mark: bool = Field(..., alias="verifiedMark")
    follower_count: int = Field(..., alias="followerCount")
    open_live: bool = Field(..., alias="openLive")
