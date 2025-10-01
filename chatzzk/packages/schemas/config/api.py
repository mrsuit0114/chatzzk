from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    """재시도 정책 설정"""

    attempts: int = 3
    wait_min_s: int = 1
    wait_max_s: int = 2


class RateLimitConfig(BaseModel):
    """Rate Limit 정책 설정"""

    max_rate: int = 5  # 시간당 최대 요청 수
    time_period: int = 1  # 시간 기준 (초)


class BaseHttpConfig(BaseModel):
    retry: RetryConfig = Field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    default_headers: dict = Field(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
    )


class ChzzkApiConfig(BaseModel):
    channel_info_template: str
    channel_vods_info_template: str
    vod_info_template: str
    vod_chats_template: str
    vod_url_template: str

    vod_manifest_headers: dict = Field({"Accept": "application/dash+xml"})
    dash_ns: dict = Field({"mpd": "urn:mpeg:dash:schema:mpd:2011"})

    http_proxy: str = Field(None)
    https_proxy: str = Field(None)


class ApiClientConfig(BaseModel):
    """API 클라이언트의 모든 동작 설정을 포함하는 모델"""

    base_http: BaseHttpConfig = Field(default_factory=BaseHttpConfig)
    chzzk_api: ChzzkApiConfig = Field(default_factory=ChzzkApiConfig)
