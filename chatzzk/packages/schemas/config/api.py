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


class ApiClientConfig(BaseModel):
    """API 클라이언트의 모든 동작 설정을 포함하는 모델"""

    retry: RetryConfig = Field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
