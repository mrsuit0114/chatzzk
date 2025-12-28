from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from chatzzk_core.constants import EntryTypeCode, PlatformCode, StreamWindowConstant


class CamelBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,  # 예: meta_info -> metaInfo
        populate_by_name=True,  # Python 코드에서 snake_case 필드명 사용 허용
    )


class AnalysisIntervals(CamelBaseModel):
    chapter_step: int = Field(StreamWindowConstant.CHAPTER_SIZE, description="챕터 단위 시간 (ms)")
    segment_step: int = Field(StreamWindowConstant.SEGMENT_SIZE, description="세그먼트 단위 시간 (ms)")
    clip_step: int = Field(StreamWindowConstant.CLIP_SIZE, description="클립(그래프) 단위 시간 (ms)")


class DashboardMetaInfo(CamelBaseModel):
    platform: PlatformCode
    title: str
    channel_id: str = Field(description="platform_channel_id")
    channel_name: str
    video_no: str
    publish_date: datetime | str
    duration: int = Field(..., description="영상 전체 길이 (s)")
    intervals: AnalysisIntervals = Field(default=AnalysisIntervals())


class StatSeries(CamelBaseModel):
    volume: list[float]
    momentum: list[float]


class DashboardStats(CamelBaseModel):
    clip: StatSeries = Field(..., description="clip window 단위 상세 그래프 데이터")
    segment: StatSeries = Field(..., description="segment window 단위 요약 그래프 데이터")
    atmosphere: dict[str, float]


class SegmentPeak(CamelBaseModel):
    peak_ts: int = Field(..., description="Peak 발생 시점의 타임스탬프 (ms)")
    peak_vl: float = Field(..., description="해당 시점의 Volume 값")
    peak_mmt: float = Field(..., description="해당 시점의 Momentum 값")


class SegmentItem(CamelBaseModel):
    txt: str = Field(..., description="세그먼트 요약 텍스트")
    kwd: list[str] = Field(..., description="주요 키워드 리스트")
    sc: float = Field(..., description="해당 세그먼트의 중요도/흥미도 점수 (Score)")
    atmo: str

    vol_peak: SegmentPeak = Field(..., description="Volume Peak 정보")
    mmt_peak: SegmentPeak = Field(..., description="Momentum Peak 정보")


class ChapterItem(CamelBaseModel):
    title: str
    txt: str


class DashboardResponse(CamelBaseModel):
    version: Literal["1.0"] = "1.0"
    meta_info: DashboardMetaInfo
    stats: DashboardStats
    segments: list[SegmentItem]
    chapters: list[ChapterItem]


class StreamLogItem(CamelBaseModel):
    ts: int
    ty: EntryTypeCode
    u: str | None = None
    c: str


class StreamLogResponse(CamelBaseModel):
    version: Literal["1.0"] = "1.0"
    stream_logs: list[StreamLogItem]
