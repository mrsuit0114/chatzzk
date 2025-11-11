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
    player_message_time: int

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
            player_message_time=chat.player_message_time,
            donation_type=chat.extras.donation_type,
            is_anonymous=chat.extras.is_anonymous,
            nickname=chat.extras.nickname,
            os_type=chat.extras.os_type,
            pay_amount=chat.extras.pay_amount,
            subscription_tier=chat.profile.subscription_tier,
            subscription_accumulative_month=chat.profile.subscription_accumulative_month,
            user_role_code=chat.profile.user_role_code,
        )


# class VADTimestampEntry(BaseModel):
#     # asr에서 사용하는 목적이므로 샘플 기준
#     start: int
#     end: int

# class ASREntry(BaseModel):
#     # 서비스에서 제공될 것이므로 시간단위
#     start_s: float
#     end_s: float
#     text: str
