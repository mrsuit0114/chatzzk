from datetime import timedelta

from pydantic import BaseModel, Field

from chatzzk_core.constants import ChzzkVODFilterConstant


class ChzzkVODDiscoveryConfig(BaseModel):
    min_duration_s: int = Field(
        default=ChzzkVODFilterConstant.MIN_DURATION_S, description="최소 영상 길이 (초), default: 30분"
    )
    min_publish_date_age: timedelta = Field(
        default=ChzzkVODFilterConstant.MIN_PUBLISH_DATE_AGE,
        description="수집할 영상의 최소 게시 기간, default: 30분",
    )
    allow_adult: bool = Field(
        default=ChzzkVODFilterConstant.ALLOW_ADULT, description="adult 영상의 수집 여부, default: False"
    )
    live_pv: int = Field(
        default=ChzzkVODFilterConstant.LIVE_PV, description="수집할 영상의 생방송 최소 시청 횟수, default: 0"
    )


class VODDiscoveryServiceConfig(BaseModel):
    chzzk: ChzzkVODDiscoveryConfig = Field(default_factory=ChzzkVODDiscoveryConfig)
