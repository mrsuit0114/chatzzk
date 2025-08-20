# common/src/common/schemas/service_codes.py

from enum import IntEnum


class PromptType(IntEnum):
    CHAT = 100
    DONATION = 1000
    ASR = 10000


CHZZK_MESSAGE_TYPE_CODE_TO_PROMPT_TYPE = {
    1: PromptType.CHAT,
    10: PromptType.DONATION,
}

ASR_PAY_AMOUNT = 0
