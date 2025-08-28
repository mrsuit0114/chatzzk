# context, summary의 구조 정의
# VodContextLine, VodSummary

from enum import IntEnum

from pydantic import BaseModel, Field, field_validator


class ContextType(IntEnum):
    CHAT = 100
    DONATION = 1000
    ASR = 10000


class VodContextEntry(BaseModel):
    timestamp_ms: int
    type: ContextType
    content: str
    pay_amount: int


class VodSummary(BaseModel):
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


"""
ContextType를 사용한 VodContextEntry의 동작 과정

저장하는 상황에서:
CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE_CODE.get(chzzk_code)의 결과로 VodContextEntry를 구축할 때 검증됨

저장과정:
new_context.json()에서 enum멤버를 해당하는 원시 값으로 자동 변환됨

사용하는 과정:
context_item = VodContextEntry.parse_obj(raw_data)에서 type_code의 값을 검증함


"""
