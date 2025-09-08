from pydantic import BaseModel, Field, field_validator

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


class ChzzkVod(BaseModel):
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

    class Config:
        # Pydantic이 alias를 사용하여 파싱하도록 설정
        populate_by_name = True
