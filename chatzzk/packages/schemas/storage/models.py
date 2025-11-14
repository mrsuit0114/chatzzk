# 저장할 때의 포멧의 스키마를 정의함 -> api_models는 좀 더 폭 넓게 받아오고 저장과 사용은 필요한 데이터에 대해서만 정의
# 공통으로 다룰 수 있는 데이터 - summary, meta_summary, asr_entries.jsonl,
# 추후에 바뀔지 모르므로 우선 하나의 파일에서만 관리


from pydantic import BaseModel

from chatzzk.packages.constants.chzzk import OsType, UserRoleCode
from chatzzk.packages.schemas.api_models.chzzk import ChzzkVideoChat


class ChzzkChatEntry(BaseModel):
    """
    ChzzkVideoChat을 입력받음
    중복된 필드 없이 저장할 필요가 있는 필드만 구성
    """

    user_id_hash: str
    content: str
    timestamp_ms: int

    donation_type: str | None
    is_anonymous: bool | None
    nickname: str | None
    os_type: OsType | None
    pay_amount: int | None
    subscription_tier: int | None
    subscription_accumulative_month: int | None
    user_role_code: UserRoleCode | None

    @classmethod
    def from_video_chat(cls, chat: ChzzkVideoChat) -> "ChzzkChatEntry":
        return cls(
            user_id_hash=chat.user_id_hash,
            content=chat.content,
            timestamp_ms=chat.player_message_time,
            donation_type=chat.extras.donation_type,
            is_anonymous=chat.extras.is_anonymous,
            nickname=chat.extras.nickname,
            os_type=chat.extras.os_type,
            pay_amount=chat.extras.pay_amount,
            subscription_tier=chat.profile.subscription_tier,
            subscription_accumulative_month=chat.profile.subscription_accumulative_month,
            user_role_code=chat.profile.user_role_code,
        )


class VADTimestampEntry(BaseModel):
    start_sample: int
    end_sample: int

    @classmethod
    def from_vad_timestamp(cls, timestamp: dict[str, int]) -> "VADTimestampEntry":
        return cls(start_sample=timestamp["start"], end_sample=timestamp["end"])


class ASREntry(BaseModel):
    timestamp_ms: int
    text: str
    end_ms: int
    start_ms: int

    @classmethod
    def from_asr_result(cls, start_sample: int, end_sample: int, transcription: str, sample_rate: int) -> "ASREntry":
        start_ms = int(start_sample / sample_rate * 1000)
        end_ms = int(end_sample / sample_rate * 1000)
        return cls(timestamp_ms=(start_ms + end_ms) // 2, start_ms=start_ms, end_ms=end_ms, text=transcription)
