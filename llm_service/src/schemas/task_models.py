from typing import Any

from pydantic import BaseModel, Field

"""-------------------------summary----------------------------"""


class BroadcastMetadata(BaseModel):
    category: str = Field(...)
    streamer_name: str = Field(...)
    streamer_nicknames: list[str] = Field(...)
    fan_nicknames: list[str] = Field(...)
    streamer_infos: list[str] = Field(...)

    # 프롬프트에 삽입될 문자열을 생성하는 헬퍼 메서드
    def to_prompt_string(self) -> str:
        streamer_nicknames = ", ".join(self.streamer_nicknames)
        fan_nicknames = ", ".join(self.fan_nicknames)
        streamer_infos = ", ".join(self.streamer_infos)

        return (
            f"방송 카테고리: {self.category}\n"
            f"스트리머 이름: {self.streamer_name}\n"
            f"스트리머 호칭: {streamer_nicknames}\n"
            f"시청자 호칭: {fan_nicknames}\n"
            f"스트리머 정보: {streamer_infos}"
        )


class PlatformMetadata(BaseModel):
    platform_name: str = Field(...)
    donation_currency: str = Field(...)

    # 프롬프트에 삽입될 문자열을 생성하는 헬퍼 메서드
    def to_prompt_string(self) -> str:
        return f"플랫폼 이름: {self.platform_name}\n후원 화폐 단위: {self.donation_currency}"


class ShortTermSummaryData(BaseModel):
    # 중첩된 모델을 사용하여 데이터 구조를 정의
    broadcast_metadata: BroadcastMetadata = Field(...)
    platform_metadata: PlatformMetadata = Field(...)

    prev_summary: str = Field("")
    cur_context: str = Field(...)

    # 프롬프트 빌더에 전달할 최종 딕셔너리를 생성하는 메서드
    def to_prompt_dict(self) -> dict[str, Any]:
        """프롬프트 템플릿에 직접 사용할 수 있는 형태로 데이터를 가공합니다."""
        return {
            # 각 메타데이터 모델의 to_prompt_string() 메서드를 호출
            "broadcast_metadata": self.broadcast_metadata.to_prompt_string(),
            "platform_metadata": self.platform_metadata.to_prompt_string(),
            "prev_summary": self.prev_summary,
            "cur_context": self.cur_context,
        }


"""-------------------------summary----------------------------"""
