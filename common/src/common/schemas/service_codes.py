# common/src/common/schemas/service_codes.py

from enum import IntEnum


class ContextType(IntEnum):
    CHAT = 100
    DONATION = 1000
    ASR = 10000


CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE = {
    1: ContextType.CHAT,
    10: ContextType.DONATION,
}

ASR_PAY_AMOUNT = 0
