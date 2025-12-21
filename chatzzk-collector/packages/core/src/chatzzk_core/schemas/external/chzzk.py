import json
from datetime import datetime
from typing import Annotated, Any, Generic, TypeVar
from zoneinfo import ZoneInfo

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, Json
from pydantic.alias_generators import to_camel

# 모든 시간 값이 KST기준으로 들어옴

# -----------------helper--------------------------
# KST(UTC+9)에서 UTC로 변환 (9시간 = 32400000ms)
UTC_OFFSET = 9 * 60 * 60 * 1000
KST_TZ = ZoneInfo("Asia/Seoul")
UTC_TZ = ZoneInfo("UTC")

DataT = TypeVar("DataT")


def convert_kst_to_utc(value: str) -> datetime | None:
    if isinstance(value, str):
        value_date = datetime.fromisoformat(value)
        if value_date.tzinfo is None:
            value_date = value_date.replace(tzinfo=KST_TZ)
        return value_date.astimezone(UTC_TZ)
    return None


def convert_kst_timestamp_to_utc(timestamp: int) -> int:
    """
    KST 기준 밀리초 타임스탬프를 UTC 기준 초 단위 타임스탬프로 변환합니다.
    """
    return timestamp - UTC_OFFSET


def parse_json_string_to_obj(v: Any) -> Any:
    if v is None:
        return None

    if isinstance(v, dict):
        return v

    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            try:
                return json.loads(v.replace("'", '"'))
            except json.JSONDecodeError:
                return {}


# -----------------helper--------------------------
class BaseAPIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,  # channel_id -> channelId 자동 변환
        populate_by_name=True,  # Python 코드에서 snake_case로도 데이터 생성 가능하게 함
        from_attributes=True,  # 추후 SQLAlchemy 객체에서 데이터를 읽어올 때 유용 (ORM 모드)
        extra="ignore",
    )


class ChzzkAPIResponse(BaseModel, Generic[DataT]):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    code: int
    message: str | None = None
    content: DataT | None = None


class SubscriptionPaymentAvailability(BaseAPIModel):
    iap_availability: bool | None = None
    iab_availability: bool | None = None


class ChzzkChannelInfo(BaseAPIModel):
    channel_id: str
    channel_name: str

    channel_image_url: str | None = None
    verified_mark: bool | None = None
    channel_type: str | None = None
    channel_description: str | None = None
    follower_count: int | None = None
    open_live: bool | None = None
    subscription_availability: bool | None = None
    subscription_payment_availability: SubscriptionPaymentAvailability | None = None
    ad_monetization_availability: bool | None = None
    activated_channel_badge_ids: list[str] = Field(default_factory=list)
    paid_product_sale_allowed: bool | None = None


class SimpleChannelInfo(BaseAPIModel):
    channel_id: str
    channel_name: str
    channel_image_url: str | None = None
    verified_mark: bool | None = None
    activated_channel_badge_ids: list[str] = Field(default_factory=list)


class ChzzkVODMeta(BaseAPIModel):
    video_no: Annotated[str, BeforeValidator(str)]
    video_id: str | None = None
    video_title: str | None = None
    video_type: str | None = None

    # Pydantic은 "YYYY-MM-DD HH:MM:SS" 문자열을 자동으로 datetime 객체로 변환해줍니다.
    # 단, 넘어오는 문자열에 시간대 정보가 없으면 timezone-naive(시간대 정보 없음) 상태가 됩니다.
    publish_date: Annotated[datetime, BeforeValidator(convert_kst_to_utc)] | None = None

    thumbnail_image_url: str | None = None
    trailer_url: str | None = None
    duration: int | None = None  # 초 단위
    read_count: int | None = None

    publish_date_at: Annotated[int, BeforeValidator(convert_kst_timestamp_to_utc)] | None = None

    category_type: str | None = None
    video_category: str | None = None
    video_category_value: str | None = None

    exposure: bool | None = None
    adult: bool | None = None
    clip_active: bool | None = None
    live_pv: int | None = None

    tags: list[str] = Field(default_factory=list)

    channel: SimpleChannelInfo | None = None

    blind_type: Any | None = None
    watch_timeline: Any | None = None
    paid_product_id: Any | None = None
    tv_app_viewing_policy_type: str | None = None


class ChzzkVODMetasContent(BaseAPIModel):
    page: int | None = None
    size: int | None = None
    total_count: int | None = None
    total_pages: int | None = None

    # 실제 비디오 리스트
    data: list[ChzzkVODMeta] = Field(default_factory=list)


class AdParameter(BaseAPIModel):
    tag: str | None = None


class BaseVODInfo(BaseAPIModel):
    video_no: Annotated[str, BeforeValidator(str)]
    video_id: str | None = None
    video_title: str | None = None
    video_type: str | None = None

    publish_date: Annotated[datetime, BeforeValidator(convert_kst_to_utc)] | None = None

    thumbnail_image_url: str | None = None
    trailer_url: str | None = None
    duration: int | None = None
    read_count: int | None = None

    publish_date_at: Annotated[int, BeforeValidator(convert_kst_timestamp_to_utc)] | None = None

    category_type: str | None = None
    video_category: str | None = None
    video_category_value: str | None = None
    exposure: bool | None = None
    adult: bool | None = None
    clip_active: bool | None = None
    live_pv: int | None = None

    tags: list[str] = Field(default_factory=list)

    channel: SimpleChannelInfo | None = None

    blind_type: str | None = None
    watch_timeline: str | None = None
    paid_product_id: str | None = None
    tv_app_viewing_policy_type: str | None = None


class EncodingTrack(BaseAPIModel):
    encoding_track_id: str = Field(alias="encodingTrackId")
    video_profile: str | None = Field(None, alias="videoProfile")
    video_bit_rate: int | None = Field(None, alias="videoBitRate")
    video_width: int | None = Field(None, alias="videoWidth")
    video_height: int | None = Field(None, alias="videoHeight")


class MediaItem(BaseAPIModel):
    media_id: str = Field(alias="mediaId")
    protocol: str
    path: str  # 여기가 m3u8 주소
    encoding_track: list[EncodingTrack] = Field(default_factory=list, alias="encodingTrack")


class LiveRewindPlayback(BaseAPIModel):
    meta: dict | None = None
    media: list[MediaItem] = Field(default_factory=list)


class ChzzkVODInfo(BaseVODInfo):
    paid_promotion: bool | None = None
    in_key: str | None = None

    live_open_date: Annotated[datetime, BeforeValidator(convert_kst_to_utc)] | None = None

    vod_status: str | None = None
    live_rewind_playback_json: Annotated[LiveRewindPlayback, BeforeValidator(parse_json_string_to_obj)] | None = None

    prev_video: BaseVODInfo | None = None
    next_video: BaseVODInfo | None = None

    user_adult_status: str | None = None
    ad_parameter: AdParameter | None = None

    video_chat_enabled: bool | None = None
    video_chat_channel_id: str | None = None
    paid_product: Any | None = None

    @property
    def m3u8_url(self) -> str | None:
        if not self.live_rewind_playback_json:
            return None

        for media in self.live_rewind_playback_json.media:
            if media.protocol == "HLS":
                return media.path

        if self.live_rewind_playback_json.media:
            return self.live_rewind_playback_json.media[0].path

        return None


class Badge(BaseAPIModel):
    image_url: str | None = None


class Subscription(BaseAPIModel):
    accumulative_month: int | None = None
    tier: int | None = None
    badge: Badge | None = None


class NicknameColor(BaseAPIModel):
    color_code: str | None = None


class StreamingProperty(BaseAPIModel):
    subscription: Subscription | None = None
    nickname_color: NicknameColor | None = None
    activated_achievement_badge_ids: list[str] = Field(default_factory=list)


class ProfileDetail(BaseAPIModel):
    user_id_hash: str | None = None
    nickname: str | None = None
    profile_image_url: str | None = None
    user_role_code: str | None = None
    badge: Any | None = None
    title: Any | None = None
    verified_mark: bool | None = None
    activity_badges: list[Any] = Field(default_factory=list)
    streaming_property: StreamingProperty | None = None
    viewer_badges: list[Any] = Field(default_factory=list)


class ExtrasDetail(BaseAPIModel):
    chat_type: str | None = None
    os_type: str | None = None
    streaming_channel_id: str | None = None
    emojis: dict[str, Any] | None = None
    extra_token: str | None = None
    donation_type: str | None = None
    donation_id: str | None = None
    is_anonymous: bool | None = None
    nickname: str | None = None
    pay_amount: int | None = None


class ChzzkVideoChat(BaseAPIModel):
    chat_channel_id: str | None = None

    message_time: Annotated[int, BeforeValidator(convert_kst_timestamp_to_utc)] | None = None

    user_id_hash: str | None = None
    content: str

    extras: Json[ExtrasDetail] | None = None

    message_type_code: int | None = None
    message_status_type: str | None = None

    profile: Json[ProfileDetail] | None = None

    player_message_time: int


class ChzzkVideoChatsContent(BaseAPIModel):
    next_player_message_time: int | None = None
    previous_video_chats: list[ChzzkVideoChat] | None = None
    video_chats: list[ChzzkVideoChat] | None = None
