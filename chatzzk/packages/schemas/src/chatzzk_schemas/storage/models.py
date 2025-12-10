# 스토리지에 저장하는 포멧을 정의 -> 읽을 때도 같은 포멧으로 읽음

import re

from typing import Annotated, Literal
from pydantic import BaseModel, Field, TypeAdapter, ConfigDict

from chatzzk_constants.chzzk import OsType, UserRoleCode
from chatzzk_constants.service_codes import StreamAtmosphere, EntryType, ASRHallucinationFilter, PlatformCode

_HALLUCINATION_KEYWORDS = ASRHallucinationFilter.get_keywords()


class _StreamEntry(BaseModel):
    content: str
    timestamp: int
    entry_type: Literal["CHAT", "DONATION"]


class ChzzkChatEntry(_StreamEntry):
    """
    ChzzkVideoChat을 입력받음
    중복된 필드 없이 저장할 필요가 있는 필드만 구성
    """

    user_id_hash: str
    donation_type: str | None = Field(default=None)
    is_anonymous: bool | None = Field(default=None)
    nickname: str | None = Field(default=None)
    os_type: OsType | None = Field(default=None)
    pay_amount: int | None = Field(default=None)
    subscription_tier: int | None = Field(default=None)
    subscription_accumulative_month: int | None = Field(default=None)
    user_role_code: UserRoleCode | None = Field(default=None)

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
        if self.user_role_code and self.user_role_code != UserRoleCode.COMMON_USER:
            nickname = self.nickname or "알수없음"
            return f"[{self.entry_type}] ({nickname}) {sanitized_content}"

        return f"[{self.entry_type}] {sanitized_content}"


class VADTimestampEntry(BaseModel):
    start_sample: int
    end_sample: int

    @classmethod
    def from_vad_timestamp(cls, timestamp: dict[str, int]) -> "VADTimestampEntry":
        return cls(start_sample=timestamp["start"], end_sample=timestamp["end"])


class ASREntry(_StreamEntry):
    end: int
    start: int
    entry_type: Literal["ASR"] = EntryType.ASR

    def to_prompt_str(self) -> str | None:
        if not self.content:
            return None

        # 할루시네이션 필터링
        for keyword in _HALLUCINATION_KEYWORDS:
            if keyword in self.content:
                return None

        return f"[{self.entry_type}] {self.content}"


class ScoreDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    expresiveness: int
    coherence: int
    significance: int
    participation: int = 0  # raw에서는 없기 때문에


class SummaryRawEntry(BaseModel):
    # start, end는 ms 단위
    start: int
    end: int
    summary: str
    keywords: list[str]
    atmosphere: StreamAtmosphere
    scores: ScoreDetail

    @classmethod
    def from_summary_raw_result(
        cls, start: int, end: int, summary: str, keywords: list[str], atmosphere: StreamAtmosphere, scores: ScoreDetail
    ) -> "SummaryRawEntry":
        return cls(start=start, end=end, summary=summary, keywords=keywords, atmosphere=atmosphere, scores=scores)


class SummaryEntry(BaseModel):
    summary: str
    keywords: list[str]
    atmosphere: StreamAtmosphere
    scores: ScoreDetail
    scores_avg: float


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
