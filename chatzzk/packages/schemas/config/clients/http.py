from pydantic import BaseModel

from chatzzk.packages.constants.client import AioHTTPConstant


class AioHTTPConfig(BaseModel):
    retry_attempts: int = AioHTTPConstant.RETRY_ATTEMPTS
    retry_wait_min_s: float = AioHTTPConstant.RETRY_WAIT_MIN_S
    retry_wait_max_s: float = AioHTTPConstant.RESTRY_WAIT_MAX_S
    timeout_s: float = AioHTTPConstant.TIMEOUT_S
