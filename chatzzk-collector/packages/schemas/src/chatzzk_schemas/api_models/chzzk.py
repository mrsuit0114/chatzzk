import json
from datetime import UTC, datetime, timedelta, timezone
from typing import Annotated, Any
from chatzzk_schemas.storage.models import ChzzkChatEntry
from chatzzk_constants.service_codes import EntryType

from loguru import logger  # Add logger for warnings in validators
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

# 모든 시간 값이 KST기준으로 들어오며 UTC로 관리하고 필요한 경우만 Localtime을 사용함

# -----------------helper--------------------------
# KST(UTC+9)에서 UTC로 변환 (9시간 = 32400000ms)
UTC_OFFSET_MS = 9 * 3600 * 1000
KST = timezone(timedelta(hours=9))


def to_utc_date(value: str) -> datetime | None:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    return value.astimezone(UTC)


def normalize_timestamp_to_utc(timestamp_ms: int) -> int:
    """
    KST 기준 밀리초 타임스탬프를 UTC 기준 초 단위 타임스탬프로 변환합니다.
    """
    return timestamp_ms - UTC_OFFSET_MS


class StrDictParser:
    @staticmethod
    def parse_str_to_dict(raw_data: str | dict) -> dict[str, Any]:
        if isinstance(raw_data, dict):
            return raw_data

        if isinstance(raw_data, str):
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError:
                fixed = raw_data.replace("'", '"')
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    return {}

        return {}


# -----------------helper--------------------------


class ChzzkChannelInfo(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    channel_image_url: str | None = Field(alias="channelImageUrl")
    verified_mark: bool = Field(alias="verifiedMark")
    follower_count: int = Field(alias="followerCount")
    open_live: bool = Field(alias="openLive")
    subscription_availability: bool = Field(alias="subscriptionAvailability")


class ChzzkChannelMeta(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    channel_image_url: str | None = Field(alias="channelImageUrl")
    verified_mark: bool = Field(alias="verifiedMark")


class ChzzkVODInfo(BaseModel):  # video_no를 기준으로 스트리머를 추가할 가능성도 있기 때문에 채널에 대해 값을 추가할 것
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    video_no: Annotated[str, BeforeValidator(str)] = Field(alias="videoNo")
    video_id: str | None = Field(default=None, alias="videoId")
    video_title: str = Field(alias="videoTitle")
    publish_date: Annotated[datetime, BeforeValidator(to_utc_date)] = Field(alias="publishDate")
    duration: int = Field(alias="duration")
    publish_date_at: Annotated[int, BeforeValidator(normalize_timestamp_to_utc)] = Field(alias="publishDateAt")
    category_type: str | None = Field(alias="categoryType")
    video_category: str | None = Field(alias="videoCategory")
    video_category_value: str | None = Field(alias="videoCategoryValue")
    exposure: bool = Field(alias="exposure")
    adult: bool = Field(alias="adult")
    channel_meta: ChzzkChannelMeta = Field(alias="channel")
    in_key: str | None = Field(default=None, alias="inKey")
    live_open_date: Annotated[datetime, BeforeValidator(to_utc_date)] = Field(default=None, alias="liveOpenDate")
    live_rewind_playback_json: str | None = Field(default=None, alias="liveRewindPlaybackJson")
    m3u8_url: str | None = Field(default=None)

    @model_validator(mode="after")
    def extract_m3u8_path(self) -> "ChzzkVODInfo":
        if self.live_rewind_playback_json:
            try:
                json_dict = StrDictParser.parse_str_to_dict(self.live_rewind_playback_json)
                media_list = json_dict.get("media")
                if media_list and isinstance(media_list, list) and len(media_list) > 0:
                    first_media_item = media_list[0]
                    if isinstance(first_media_item, dict):
                        self.m3u8_url = first_media_item.get("path")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse live_rewind_playback_json for video_no={self.video_no}: {e}")
                self.m3u8_url = None
        return self


class ChzzkVODMeta(BaseModel):  # api요청을 최소화하기 위해 video_no를 필터링할 조건 후보는 파싱해서 보유할 것
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    video_no: int = Field(
        alias="videoNo"
    )  # VODMeta는 직접 db에 저장되는 데이터가 아니기 때문에 성능을 위해 int로 관리함
    publish_date_at: Annotated[int, BeforeValidator(normalize_timestamp_to_utc)] = Field(alias="publishDateAt")
    duration_s: int = Field(alias="duration")
    read_count: int = Field(alias="readCount")
    category_type: str = Field(alias="categoryType")
    video_category: str = Field(alias="videoCategory")
    video_category_value: str = Field(alias="videoCategoryValue")
    adult: bool = Field(alias="adult")
    live_pv: int = Field(alias="livePv")


class ChzzkChannelVODs(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    page: int = Field(alias="page")
    size: int = Field(alias="size")
    total_count: int = Field(alias="totalCount")
    total_pages: int = Field(alias="totalPages")
    data: list[ChzzkVODMeta] = Field(alias="data")


class ChzzkVideoChatExtras(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    donation_type: str | None = Field(default=None, alias="donationType")
    donation_id: str | None = Field(default=None, alias="donationId")

    is_anonymous: bool | None = Field(
        default=None, alias="isAnonymous", description="Only present for donation events; indicates anonymity."
    )
    nickname: str | None = Field(
        default=None, alias="nickname", description="Only present for donation envent not anonymous"
    )
    os_type: str | None = Field(default=None, alias="osType", description="Only present for general chat event")
    pay_amount: int | None = Field(default=None, alias="payAmount", description="Only present for donation events")

    @model_validator(mode="before")
    def parse_video_chat_extras(cls, values: str) -> dict[str, Any]:
        return StrDictParser.parse_str_to_dict(values)


class ChzzkProfile(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    nickname: str | None = Field(default=None, alias="nickname")
    subscription_tier: int | None = Field(default=None)
    subscription_accumulative_month: int | None = Field(default=None)
    user_id_hash: str | None = Field(default=None, alias="userIdHash")
    user_role_code: str | None = Field(default=None, alias="userRoleCode")

    @model_validator(mode="before")
    def parse_chzzk_profile(cls, values: str) -> dict[str, Any]:
        values_dict = StrDictParser.parse_str_to_dict(values)

        if "streamingProperty" not in values_dict:
            return values_dict

        data = values_dict.get("streamingProperty")
        subscription = data.get("subscription", {})

        if "tier" in subscription:
            values_dict["subscription_tier"] = subscription["tier"]
        if "accumulativeMonth" in subscription:
            values_dict["subscription_accumulative_month"] = subscription["accumulativeMonth"]

        return values_dict


class ChzzkVideoChat(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    message_time: int = Field(alias="messageTime")
    user_id_hash: str = Field(alias="userIdHash")
    content: str = Field(alias="content")
    extras: ChzzkVideoChatExtras = Field(alias="extras")
    profile: ChzzkProfile = Field(alias="profile")
    player_message_time: int = Field(alias="playerMessageTime")

    def to_chat_entry(self) -> ChzzkChatEntry:
        return ChzzkChatEntry(
            user_id_hash=self.user_id_hash,
            content=self.content,
            timestamp=self.player_message_time,
            donation_type=self.extras.donation_type,
            is_anonymous=self.extras.is_anonymous,
            nickname=self.profile.nickname,
            os_type=self.extras.os_type,
            pay_amount=self.extras.pay_amount,
            subscription_tier=self.profile.subscription_tier,
            subscription_accumulative_month=self.profile.subscription_accumulative_month,
            user_role_code=self.profile.user_role_code,
            entry_type=EntryType.DONATION if self.extras.pay_amount else EntryType.CHAT,
        )


class ChzzkVODChats(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    next_player_message_time: int | None = Field(alias="nextPlayerMessageTime")
    video_chats: list[ChzzkVideoChat] = Field(alias="videoChats")
