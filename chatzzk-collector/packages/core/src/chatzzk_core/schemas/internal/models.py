# 스토리지에 저장하는 포멧을 정의 -> 읽을 때도 같은 포멧으로 읽음

import re
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from chatzzk_core.constants import ChzzkUserRoleCode
from chatzzk_core.constants.service_code import EntryType, ScoreCategory, StreamAtmosphere
from chatzzk_core.schemas.external import ChzzkVideoChat


class BaseStreamEntry(BaseModel, ABC):
    timestamp: int
    content: str
    entry_type: EntryType

    model_config = ConfigDict(use_enum_values=True)

    def __lt__(self, other: "BaseStreamEntry") -> bool:
        if not isinstance(other, BaseStreamEntry):
            return NotImplemented
        return self.timestamp < other.timestamp

    def sanitize(self) -> "BaseStreamEntry":
        return self

    # [핵심 2] 컨텍스트 변환은 필수 구현 (Assembler가 호출하므로)
    @abstractmethod
    def to_context_string(self) -> str:
        """
        LLM 입력용 컨텍스트 문자열로 변환합니다.
        LLM 입력으로 사용되지 않는 모델은 NotImplementedError를 발생시킵니다.
        """
        pass


class ChatEntry(BaseStreamEntry):
    entry_type: Literal[EntryType.CHAT, EntryType.DONATION]
    nickname: str | None = Field(default=None, description="특수 권한 유저 닉네임 (일반 유저는 None)")

    def to_context_string(self) -> str:
        prefix = f"[{self.entry_type.value}]"
        if self.nickname:
            return f"{prefix} ({self.nickname}) {self.content}"
        return f"{prefix} {self.content}"

    # 기본 sanitize는 공통적인 처리(공백 제거 등)만 수행
    def sanitize(self) -> "ChatEntry":
        content = re.sub(r"(\S)\1{2,}", r"\1\1", self.content)  # 반복 문자 축소
        content = re.sub(r"\s+", " ", content).strip()
        # Pydantic 모델은 기본적으로 불변이 아니므로 필드 수정 가능
        self.content = content
        return self


class ChzzkChatEntry(ChatEntry):
    """
    치지직 플랫폼의 특성을 반영한 ChatEntry 구현체
    """

    def sanitize(self) -> "ChzzkChatEntry":
        # 1. 부모의 기본 정규화 수행 (반복 문자 등)
        super().sanitize()

        # 2. 치지직 전용 이모지 제거 ({:emoji:})
        self.content = re.sub(r"\{:[^}]*:\}", "", self.content).strip()

        return self

    @classmethod
    def from_chzzk_video_chat(cls, chzzk_video_chat: ChzzkVideoChat) -> "ChzzkChatEntry":
        return cls(
            content=chzzk_video_chat.content,
            timestamp=chzzk_video_chat.player_message_time,
            entry_type=EntryType.DONATION
            if chzzk_video_chat.extras and chzzk_video_chat.extras.pay_amount
            else EntryType.CHAT,
            nickname=chzzk_video_chat.profile.nickname
            if (
                chzzk_video_chat.profile
                and chzzk_video_chat.profile.user_role_code
                and chzzk_video_chat.profile.user_role_code != ChzzkUserRoleCode.COMMON_USER
            )
            else None,
        )


class ASREntry(BaseStreamEntry):
    entry_type: Literal[EntryType.ASR] = EntryType.ASR
    start: int = Field(..., description="발화 시작 시점 (Sample Index 기반 환산 값)")
    end: int = Field(..., description="발화 종료 시점")

    def to_context_string(self) -> str:
        return f"[{self.entry_type.value}] {self.content}"

    def is_hallucination(self, hallucination_keywords: list[str]) -> bool:
        """환각 여부 판단"""
        if not self.content:
            return True
        return any(k in self.content for k in hallucination_keywords)

    @classmethod
    def from_asr_result(cls, start: int, end: int, content: str) -> "ASREntry":
        return cls(
            timestamp=(start + end) // 2,
            content=content,
            start=start,
            end=end,
            entry_type=EntryType.ASR,
        )


class SummaryEntry(BaseStreamEntry):
    entry_type: Literal[EntryType.SUMMARY] = EntryType.SUMMARY
    keywords: list[str] = Field(default_factory=list)
    atmosphere: StreamAtmosphere
    scores: dict[ScoreCategory, int] = Field(default_factory=dict)  # 예: {"fun": 5, "accuracy": 4}

    def to_context_string(self) -> str:
        return self.content


class MetaSummaryEntry(BaseStreamEntry):
    title: str
    entry_type: Literal[EntryType.META_SUMMARY] = EntryType.META_SUMMARY

    def to_context_string(self) -> str:
        raise NotImplementedError("MetaSummaryEntry is not intended to be used as a generation context.")
