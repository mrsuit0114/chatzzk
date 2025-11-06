from pydantic import BaseModel, Field

from chatzzk.packages.constants.chzzk import ChzzkVODFilterConstant
from chatzzk.packages.schemas.api_models.chzzk import ChzzkVODMeta


class VODFilterConfig(BaseModel):
    """VOD 필터링 조건을 정의하고, 필터링 로직을 수행하는 모델"""

    min_duration_s: int = Field(
        default=ChzzkVODFilterConstant.MIN_DURATION_S, description="최소 영상 길이 (초), default: 30분"
    )
    min_publish_date_at_age_ms: int = Field(
        default=ChzzkVODFilterConstant.MIN_PUBLISH_DATE_AT_AGE_MS,
        description="수집할 영상의 최소 게시 기간 (ms), default: 30분",
    )
    allow_adult: bool = Field(
        default=ChzzkVODFilterConstant.ALLOW_AUDLT, description="adult 영상의 수집 여부, default: False"
    )
    live_pv: int = Field(
        default=ChzzkVODFilterConstant.LIVE_PV, description="수집할 영상의 생방송 최소 시청 횟수, default: 0"
    )

    # 필터링 로직을 모델 메서드로 구현
    def is_valid(self, vod_meta: ChzzkVODMeta, cur_timestamp_utc: int) -> bool:
        if vod_meta.duration_s < self.min_duration_s:
            return False

        if vod_meta.publish_date_at > cur_timestamp_utc - self.min_publish_date_at_age_ms:
            return False
        # Ture: adult, self.allow_adult - (True, True), (False, True), (False, False) -> 수집
        # Flase: (True, False)
        if vod_meta.adult and not self.allow_adult:
            return False

        if vod_meta.live_pv < self.live_pv:
            return False

        return True


class VODDiscoveryServiceConfig(BaseModel):
    vod_filter: VODFilterConfig = Field(default_factory=VODFilterConfig)
