# context, summary의 구조 정의
# VodContextLine, VodSummary

from enum import IntEnum

from pydantic import BaseModel


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


"""
ContextType를 사용한 VodContextEntry의 동작 과정

저장하는 상황에서:
CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE_CODE.get(chzzk_code)의 결과로 VodContextEntry를 구축할 때 검증됨

저장과정:
new_context.json()에서 enum멤버를 해당하는 원시 값으로 자동 변환됨

사용하는 과정:
context_item = VodContextEntry.parse_obj(raw_data)에서 type_code의 값을 검증함


"""
