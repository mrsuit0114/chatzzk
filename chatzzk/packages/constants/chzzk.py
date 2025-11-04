from dataclasses import dataclass
from enum import Enum, IntEnum


@dataclass
class ChzzkDBDefaults:
    PLATFORM_CHANNEL_ID_MAX_LEN = 100
    CHANNEL_NAME_MAX_LEN = 100
    VIDEO_TITLE_MAX_LEN = 100
    VIDEO_CATEGORY_VALUE_MAX_LEN = 100


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
