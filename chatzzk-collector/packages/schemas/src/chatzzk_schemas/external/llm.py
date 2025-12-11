from typing import Literal, Optional
from pydantic import BaseModel
from chatzzk_constants.service_codes import StreamAtmosphere
from chatzzk_schemas.storage.models import SummaryRawEntry, StreamEntry

# _Params: 프롬프트를 구성할 때 필요한 데이터의 스키마를 정의
# _Input: 실제로 프롬프트에 사용하기 위해 변환된 데이터


class PlatformMetadata(BaseModel):
    platform_name: Literal["치지직", "숲"]
    donation_unit: Literal["치즈", "별풍선"]
    additional_informations: list[str] | None = None


class ChannelMetadata(BaseModel):
    channel_name: str
    streamer_nicknames: list[str]
    streamer_sex: Literal["남성", "여성"]
    fan_nicknames: list[str] | None = None
    additional_informations: list[str] | None = None


class StreamSegmentAnalysisParams(BaseModel):
    # 시스템 프롬프트의 param은 비즈니스 수준에서 고정되지만 prompt building 용이성을 위해 해당 모델에서 관리함
    atmosphere_list: list[StreamAtmosphere] = list(a.value for a in StreamAtmosphere)

    platform_metadata: PlatformMetadata
    channel_metadata: ChannelMetadata

    previous_summary: str | None = None

    broadcast_logs: list[StreamEntry]


class StreamSegmentAnalysisInput(BaseModel):
    atmosphere_list: str

    platform_metadata: str
    channel_metadata: str
    previous_summary: str | None = None
    broadcast_logs: str

    @classmethod
    def from_analysis_params(cls, params: StreamSegmentAnalysisParams) -> Optional["StreamSegmentAnalysisInput"]:
        if not params.broadcast_logs:
            return None
        platform_metadata = (
            f"플랫폼 명: {params.platform_metadata.platform_name}\n후원 단위: {params.platform_metadata.donation_unit}"
        )
        if params.platform_metadata.additional_informations:
            platform_metadata += f"\n추가 정보: {'. '.join(params.platform_metadata.additional_informations)}"

        channel_name = f'채널 명: "{params.channel_metadata.channel_name}"'
        streamer_nicknames = "\n스트리머 호칭: " + ", ".join(
            f'"{nickname}"' for nickname in params.channel_metadata.streamer_nicknames
        )
        streamer_sex = "\n스트리머 성별: " + params.channel_metadata.streamer_sex
        fan_nicknames = (
            "\n팬 호칭: " + ", ".join(f'"{nickname}"' for nickname in params.channel_metadata.fan_nicknames)
            if params.channel_metadata.fan_nicknames
            else ""
        )
        channel_metadata = channel_name + streamer_nicknames + streamer_sex + fan_nicknames
        if params.channel_metadata.additional_informations:
            channel_metadata += "\n추가 정보: " + ", ".join(params.channel_metadata.additional_informations)

        previous_summary = (
            ("이전 요약: " + params.previous_summary) if params.previous_summary else "이전 요약이 없습니다."
        )

        broadcast_logs = "현재 방송 컨텍스트:\n" + "\n".join(
            s for log in params.broadcast_logs if (s := log.to_prompt_str())
        )

        return cls(
            atmosphere_list=", ".join(params.atmosphere_list),
            platform_metadata=platform_metadata,
            channel_metadata=channel_metadata,
            previous_summary=previous_summary,
            broadcast_logs=broadcast_logs,
        )


class ScoreDetail(BaseModel):
    expresiveness: int
    coherence: int
    significance: int


class StreamSegmentAnalysisResponse(BaseModel):
    summary: str
    keywords: list[str]
    atmosphere: StreamAtmosphere
    scores: ScoreDetail

    def to_summary_raw_entry(self, start: int, end: int) -> SummaryRawEntry:
        return SummaryRawEntry(
            start=start,
            end=end,
            summary=self.summary,
            keywords=self.keywords,
            atmosphere=self.atmosphere,
            scores=self.scores.model_dump(),
        )
