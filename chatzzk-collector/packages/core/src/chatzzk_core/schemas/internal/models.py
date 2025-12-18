# 스토리지에 저장하는 포멧을 정의 -> 읽을 때도 같은 포멧으로 읽음

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from chatzzk_core.constants.chzzk import UserRoleCode
from chatzzk_core.constants.service_codes import ASRHallucinationFilter, EntryType, PlatformCode
from chatzzk_core.schemas.external.chzzk import ChzzkVideoChat

_HALLUCINATION_KEYWORDS = ASRHallucinationFilter.get_keywords()


class _StreamEntry(BaseModel):
    content: str
    timestamp: int
    entry_type: str


class ChzzkChatEntry(_StreamEntry):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    nickname: str | None = Field(default=None)
    entry_type: Literal["CHAT", "DONATION"]

    @classmethod
    def _sanitize_content(cls, content: str) -> str:
        content = re.sub(r"\{:[^}]*:\}", "", content)  # 이모지 제거
        content = re.sub(r"(\S)\1{2,}", r"\1\1", content)  # 글자 반복 축소
        content = re.sub(r"\s+", " ", content)  # 연속된 공백(2개 이상)을 1개로 통일
        return content.strip()

    def to_prompt_str(self) -> str | None:
        if not self.content:
            return None

        sanitized_content = self._sanitize_content(self.content)
        if not sanitized_content:
            return None

        # 일반 유저가 아닌 경우에만 sender 정보(닉네임)를 포함
        if self.nickname:
            return f"[{self.entry_type}] ({self.nickname}) {sanitized_content}"

        return f"[{self.entry_type}] {sanitized_content}"

    @classmethod
    def from_video_chat(cls, chzzk_video_chat: ChzzkVideoChat) -> "ChzzkChatEntry":
        return cls(
            content=chzzk_video_chat.content,
            timestamp=chzzk_video_chat.player_message_time,
            entry_type=EntryType.DONATION if chzzk_video_chat.extras.pay_amount else EntryType.CHAT,
            nickname=chzzk_video_chat.profile.nickname
            if (
                chzzk_video_chat.profile
                and chzzk_video_chat.profile.user_role_code
                and chzzk_video_chat.profile.user_role_code != UserRoleCode.COMMON_USER
            )
            else None,
        )


class VADTimestampEntry(BaseModel):
    start_sample: int
    end_sample: int

    @classmethod
    def from_vad_timestamp(cls, timestamp: dict[str, int]) -> "VADTimestampEntry":
        return cls(start_sample=timestamp["start"], end_sample=timestamp["end"])


class ASREntry(_StreamEntry):
    start: int
    end: int

    entry_type: Literal["ASR"] = EntryType.ASR

    def to_prompt_str(self) -> str | None:
        if not self.content:
            return None

        # 할루시네이션 필터링
        for keyword in _HALLUCINATION_KEYWORDS:
            if keyword in self.content:
                return None

        return f"[{self.entry_type}] {self.content}"

    @classmethod
    def from_asr_result(cls, start: int, end: int, content: str) -> "ASREntry":
        return cls(
            timestamp=(start + end) // 2,
            content=content,
            start=start,
            end=end,
            entry_type=EntryType.ASR,
        )


# class ScoreDetail(BaseModel):
#     model_config = ConfigDict(extra="ignore")
#     expresiveness: int
#     coherence: int
#     significance: int
#     participation: int = 0  # raw에서는 없기 때문에


# class SummaryEntry(BaseModel):
#     start: int
#     end: int
#     summary: str
#     keywords: list[str]
#     atmosphere: StreamAtmosphere
#     scores: ScoreDetail

#     @classmethod
#     def from_stream_segment_analysis_response(cls, start: int, end: int, response: StreamSegmentAnalysisResponse) -> "SummaryEntry":
#         return cls(
#             start=start,
#             end=end,
#             summary=response.summary,
#             keywords=response.keywords,
#             atmosphere=response.atmosphere,
#             scores=response.scores,
#         )


ChzzkStreamEntry = Annotated[ChzzkChatEntry | ASREntry, Field(discriminator="entry_type")]

StreamEntry = ChzzkStreamEntry  # | YoutubeStreamEntry

ChzzkStreamEntryAdapter = TypeAdapter(ChzzkStreamEntry)


def get_stream_entry_adapter(platform_code: PlatformCode) -> TypeAdapter[StreamEntry]:
    if platform_code == PlatformCode.CHZZK:
        return ChzzkStreamEntryAdapter
    # elif platform_code == PlatformCode.YOUTUBE:
    #     return YoutubeStreamEntryAdapter
    else:
        raise ValueError(f"Unsupported platform code: {platform_code}")
