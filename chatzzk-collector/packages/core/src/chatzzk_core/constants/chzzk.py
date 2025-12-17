from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, IntEnum


@dataclass
class ChzzkAPIConstant:
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    VOD_MANIFEST_HEADERS = {"Accept": "application/dash+xml"}

    CHANNEL_INFO_URL = "https://api.chzzk.naver.com/service/v1/channels/{channel_id}"
    VOD_METAS_URL = "https://api.chzzk.naver.com/service/v1/channels/{channel_id}/videos?sortType=LATEST&pagingType=PAGE&page={page_idx}&size={page_size}"

    VOD_INFO_URL = "https://api.chzzk.naver.com/service/v2/videos/{video_no}"
    VOD_CHATS_URL = (
        "https://api.chzzk.naver.com/service/v1/videos/{video_no}/chats?playerMessageTime={player_message_time}"
    )
    VOD_PLAYBACK_URL = "https://apis.naver.com/neonplayer/vodplay/v2/playback/{video_id}?key={in_key}"

    PAGE_SIZE = 30
    LAST_END_TIME_OFFSET = 1000
    CHUNK_SIZE = 262144
    RS_IDX = 0  # lowest resolution idx

    DASH_NS = {"mpd": "urn:mpeg:dash:schema:mpd:2011"}

    RATE_LIMIT_MAX_RATE = 2
    RATE_LIMIT_TIME_PERIOD = 0.1


@dataclass
class ChzzkMessageTypeCode(IntEnum):
    CHAT = 1
    DONATION = 10
    SYSTEM = 30


@dataclass
class SubscriptionTier(IntEnum):
    NO_SUBSCRIPTION = 0
    GENERAL = 1
    PREMIUM = 2


@dataclass
class OsType(str, Enum):
    IOS = "IOS"
    PC = "PC"
    AOS = "AOS"


@dataclass
class UserRoleCode(str, Enum):
    COMMON_USER = "common_user"
    STREAMING_CHAT_MANAGER = "streaming_chat_manager"
    STREAMING_CHANNEL_OWNER = "streaming_channel_owner"
    STREAMING_CHANNEL_MANAGER = "streaming_channel_manager"
    STREAMER = "streamer"  # channel_owner와 별개로 존재함, owner가 streamer 본인이 아닌가 채팅에서는 streamer로 확인


@dataclass
class ChzzkVODFilterConstant:
    MIN_DURATION_S = 1800
    MIN_PUBLISH_DATE_AGE = timedelta(minutes=30)
    ALLOW_AUDLT = False
    LIVE_PV = 0
