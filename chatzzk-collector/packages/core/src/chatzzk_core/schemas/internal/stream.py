import re
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from chatzzk_core.constants import ChzzkUserRoleCode, EntryType, StreamAtmosphere
from chatzzk_core.schemas.external import ChzzkVideoChat
from chatzzk_core.schemas.internal.llm import ChapterSummaryGenerationOutput, SegmentSummaryGenerationOutput


class BaseStreamEntry(BaseModel):
    # 스트림 엔트리의 기본 클래스
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True, alias_generator=to_camel)

    timestamp: int
    content: str | list[dict[str, Any]]
    entry_type: EntryType

    def __lt__(self, other: "BaseStreamEntry") -> bool:
        if not isinstance(other, BaseStreamEntry):
            return NotImplemented
        return self.timestamp < other.timestamp

    def sanitize(self) -> "BaseStreamEntry":
        return self


# 1단계: 문구/복붙 반복용 (비탐욕적 매칭)
RE_PHRASE_REPEAT = re.compile(r"(?P<p>.+?)(?:\s?(?P=p))+")

# 2단계: 단일 문자 3회 이상 반복용
RE_CHAR_REPEAT = re.compile(r"(\S)\1{2,}")

# 3단계: 연속 공백 정리용
RE_WHITESPACE = re.compile(r"\s+")


def shrink_phrase(match):
    phrase = match.group("p").strip()
    if len(phrase) > 1:
        return f"{phrase} {phrase}"
    return f"{phrase}{phrase}"


def preprocess_chat(content: str) -> str:
    content = RE_PHRASE_REPEAT.sub(shrink_phrase, content)
    content = RE_CHAR_REPEAT.sub(r"\1\1", content)
    content = RE_WHITESPACE.sub(" ", content).strip()

    return content


class ChatEntry(BaseStreamEntry):
    entry_type: Literal[EntryType.CHAT, EntryType.DONATION]
    nickname: str | None = Field(default=None, description="특수 권한 유저 닉네임 (일반 유저는 None)")

    def to_context_string(self) -> str:
        if self.nickname:
            return f"[{self.entry_type}-{self.nickname}] {self.content}"
        return f"[{self.entry_type}] {self.content}"

    def sanitize(self) -> "ChatEntry":
        self.content = preprocess_chat(self.content)
        return self


class ChzzkChatEntry(ChatEntry):
    """
    치지직 플랫폼의 특성을 반영한 ChatEntry 구현체
    """

    def sanitize(self) -> "ChzzkChatEntry":
        if "!투표" in self.content:
            self.content = ""

        self.content = re.sub(r"\{:[^}]*:\}", "", self.content).strip()

        super().sanitize()
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


def _compress_char_repetition(text: str, max_repeat: int = 3) -> str:
    pattern = re.compile(r"(.)\1{" + str(max_repeat) + r",}")
    return pattern.sub(lambda m: m.group(1) * max_repeat, text)


def _compress_consecutive_words(text: str, max_repeat: int = 3) -> str:
    tokens = text.split()
    if not tokens:
        return text

    result = []
    prev = None
    count = 0

    for token in tokens:
        if token == prev:
            if count < max_repeat:
                result.append(token)
            count += 1
        else:
            prev = token
            count = 1
            result.append(token)

    return " ".join(result)


def _preprocess_asr(content: str) -> str:
    content = _compress_char_repetition(content)
    content = _compress_consecutive_words(content)
    return content


class ASREntry(BaseStreamEntry):
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

    def sanitize(self) -> "ASREntry":
        self.content = _preprocess_asr(self.content)
        return self

    @classmethod
    def from_asr_result(cls, start: int, end: int, content: str) -> "ASREntry":
        return cls(
            timestamp=(start + end) // 2,
            content=content,
            start=start,
            end=end,
            entry_type=EntryType.ASR,
        )


class SegmentSummaryEntry(BaseStreamEntry):
    entry_type: Literal[EntryType.SEGMENT_SUMMARY] = EntryType.SEGMENT_SUMMARY
    keywords: list[str] = Field(default_factory=list)
    atmosphere: StreamAtmosphere

    def to_context_string(self) -> str:
        return f"{self.content}"

    @classmethod
    def from_generation_output(
        cls,
        timestamp: int,
        generation_output: SegmentSummaryGenerationOutput,
    ) -> "SegmentSummaryEntry":
        return cls(
            timestamp=timestamp,
            content=generation_output.summary_text,
            entry_type=EntryType.SEGMENT_SUMMARY,
            keywords=generation_output.keywords,
            atmosphere=generation_output.atmosphere,
        )


class ChapterSummaryEntry(BaseStreamEntry):
    title: str
    entry_type: Literal[EntryType.CHAPTER_SUMMARY] = EntryType.CHAPTER_SUMMARY

    @classmethod
    def from_generation_output(
        cls,
        timestamp: int,
        generation_output: ChapterSummaryGenerationOutput,
    ) -> "ChapterSummaryEntry":
        topics_data = [topic.model_dump() for topic in generation_output.key_topics]

        return cls(
            timestamp=timestamp,
            content=topics_data,
            entry_type=EntryType.CHAPTER_SUMMARY,
            title=generation_output.title,
        )


class StreamEntryDict(TypedDict):
    timestamp: int
    content: str


class SegmentSummaryDict(TypedDict):
    timestamp: int
    content: str
    atmosphere: StreamAtmosphere
    keywords: list[str]


class TopicItemDict(TypedDict):
    timestamp: str
    topic: str


class ChapterSummaryDict(TypedDict):
    timestamp: int
    content: list[TopicItemDict]
    title: str
