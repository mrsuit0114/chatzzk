import re
from abc import ABC
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from chatzzk_core.constants import ChzzkUserRoleCode, EntryType, ScoreCategory, StreamAtmosphere
from chatzzk_core.schemas.external import ChzzkVideoChat
from chatzzk_core.schemas.internal.llm import SegmentSummaryGenerationOutput
from chatzzk_core.schemas.internal.shared import ContextRenderable


class BaseStreamEntry(BaseModel, ABC):
    # 스트림 엔트리의 기본 클래스
    model_config = ConfigDict(use_enum_values=True)

    timestamp: int
    content: str
    entry_type: EntryType

    def __lt__(self, other: "BaseStreamEntry") -> bool:
        if not isinstance(other, BaseStreamEntry):
            return NotImplemented
        return self.timestamp < other.timestamp

    def sanitize(self) -> "BaseStreamEntry":
        return self


class ChatEntry(BaseStreamEntry, ContextRenderable):
    entry_type: Literal[EntryType.CHAT, EntryType.DONATION]
    nickname: str | None = Field(default=None, description="특수 권한 유저 닉네임 (일반 유저는 None)")

    def to_context_string(self) -> str:
        prefix = f"[{self.entry_type}]"
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


class ASREntry(BaseStreamEntry, ContextRenderable):
    entry_type: Literal[EntryType.ASR] = EntryType.ASR
    start: int = Field(..., description="발화 시작 시점 (Sample Index 기반 환산 값)")
    end: int = Field(..., description="발화 종료 시점")

    def to_context_string(self) -> str:
        return f"[{self.entry_type}] {self.content}"

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


class SegmentSummaryEntry(BaseStreamEntry, ContextRenderable):
    entry_type: Literal[EntryType.SEGMENT_SUMMARY] = EntryType.SEGMENT_SUMMARY
    keywords: list[str] = Field(default_factory=list)
    atmosphere: StreamAtmosphere
    scores: dict[ScoreCategory, int] = Field(default_factory=dict)

    def to_context_string(self) -> str:
        return self.content

    @classmethod
    def from_generation_output(
        cls,
        timestamp: int,
        generation_output: SegmentSummaryGenerationOutput,
    ) -> "SegmentSummaryEntry":
        scores_dict = cast(dict[ScoreCategory, int], generation_output.scores.model_dump())

        return cls(
            timestamp=timestamp,
            content=generation_output.summary_text,
            entry_type=EntryType.SEGMENT_SUMMARY,
            keywords=generation_output.keywords,
            atmosphere=generation_output.atmosphere,
            scores=scores_dict,
        )


class ChapterSummaryEntry(BaseStreamEntry, ContextRenderable):
    title: str
    entry_type: Literal[EntryType.CHAPTER_SUMMARY] = EntryType.CHAPTER_SUMMARY

    def to_context_string(self) -> str:
        return self.content
