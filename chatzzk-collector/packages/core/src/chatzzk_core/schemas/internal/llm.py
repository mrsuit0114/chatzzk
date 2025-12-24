from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from chatzzk_core.constants.service_code import StreamAtmosphere


class PlatformMetadataContext(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    platform_name: str
    donation_unit: str | None = None

    def to_context_string(self) -> str:
        platform_lines = []
        platform_lines.append(f"- 플랫폼 이름: {self.platform_name}")
        if self.donation_unit is not None:
            platform_lines.append(f"- 후원 단위: {self.donation_unit}")
        return "\n".join(platform_lines)


# ChannelLLMContext의 llm_context을 구성할 때도 이 모델을 사용할 것
class ChannelMetadataContext(BaseModel):
    model_config = ConfigDict(extra="ignore")
    streamer_nicknames: list[str] = Field(default_factory=list)
    streamer_sex: Literal["남성", "여성"] = "남성"
    fan_nicknames: list[str] = Field(default_factory=list)
    additional_info: list[str] = Field(default_factory=list)

    def to_context_string(self) -> str:
        channel_lines = []

        # 따옴표(")로 감싸서 고유명사임을 명확히 함
        nicknames = ", ".join(f'"{name}"' for name in self.streamer_nicknames)
        channel_lines.append(f"- 스트리머 호칭: {nicknames}")

        channel_lines.append(f"- 성별: {self.streamer_sex}")
        if self.fan_nicknames:
            fan_names = ", ".join(f'"{name}"' for name in self.fan_nicknames)
            channel_lines.append(f"- 팬 호칭: {fan_names}")

        if self.additional_info:
            channel_lines.append("- 추가 정보:")
            for info in self.additional_info:
                info = info.strip()
                if info:
                    if not info.endswith("."):
                        info += "."
                    channel_lines.append(f"  * {info}")

        return "\n".join(channel_lines)


class MetadataContext(BaseModel):
    platform: PlatformMetadataContext
    channel: ChannelMetadataContext

    def to_context_string(self) -> str:
        return f"{self.platform.to_context_string()}\n{self.channel.to_context_string()}"


class SegmentSummaryGenerationInput(BaseModel):
    # 프롬프트 생성을 위해 서비스에서 제공해야하는 최종 모델이자 prompt manager의 해당 메서드가 알고 있는 모델 -> **model_dump()를 사용할 것
    # 필드끼리는 템플릿에서 개행으로 구분되어 있으므로 필드 내부의 개행만 고려할 것
    atmosphere_list: str = ", ".join(atmo.value for atmo in StreamAtmosphere)

    metadata_context: str
    previous_summary: str = Field(default="이전 요약이 없습니다.", description="이전 구간 요약문")
    broadcast_logs: str = Field(..., description="방송 로그 (ASR, CHAT, DONATION), 없는 경우 llm API 호출 불가")

    @classmethod
    def assemble(
        cls,
        platform_metadata_context: PlatformMetadataContext,
        channel_metadata_context: ChannelMetadataContext,
        previous_summary: str,
        broadcast_logs: str,
    ) -> "SegmentSummaryGenerationInput":
        metadata_context = MetadataContext(platform=platform_metadata_context, channel=channel_metadata_context)
        return cls(
            metadata_context=metadata_context.to_context_string(),
            previous_summary=previous_summary,
            broadcast_logs=broadcast_logs,
        )


class EvaluationScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expressiveness: int = Field(
        ..., description="방송 로그(ASR, CHAT, DONATION)이 얼마나 구체적이고 풍부한 표현을 담고 있는가?", ge=1, le=10
    )
    reaction_unity: int = Field(
        ..., description="시청자들의 반응이 통일된 구간이 얼마나 명확하게 구분되는가?", ge=1, le=10
    )
    significance: int = Field(..., description="제공된 구간이 하이라이트로서 얼마나 가치가 있는가?", ge=1, le=10)


# structured output - 필드 이름, description, enum(type), 중첩 구조 등이 성능과 비용에 영향을 미침
class SegmentSummaryGenerationOutput(BaseModel):
    summary_text: str = Field(..., description="방송 내용을 요약한 텍스트")

    atmosphere: StreamAtmosphere = Field(
        ..., description="주어진 구간에서 시청자(CHAT, DONATION)가 느끼는 지배적인 방송 분위기"
    )

    keywords: list[str] = Field(
        ..., description="stream logs와 요약문을 관통하는 키워드 리스트 (5개 이내)", min_length=3, max_length=5
    )

    scores: EvaluationScores = Field(..., description="방송 내용에 대한 정량적 평가")


class ChapterSummaryGenerationInput(BaseModel):
    metadata_context: str
    segment_summaries: str  # 요약문 리스트, 개행으로 구분

    @classmethod
    def assemble(
        cls,
        platform_metadata_context: PlatformMetadataContext,
        channel_metadata_context: ChannelMetadataContext,
        segment_summaries: str,
    ) -> "ChapterSummaryGenerationInput":
        metadata_context = MetadataContext(platform=platform_metadata_context, channel=channel_metadata_context)
        return cls(
            metadata_context=metadata_context.to_context_string(),
            segment_summaries=segment_summaries,
        )


class ChapterSummaryGenerationOutput(BaseModel):
    title: str = Field(..., description="챕터 내용을 대표하는 제목")
    summary_text: str = Field(..., description="챕터 내용을 요약한 텍스트")
