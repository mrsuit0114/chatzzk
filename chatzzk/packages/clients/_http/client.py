import aiohttp
from aiolimiter import AsyncLimiter
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_random

from chatzzk.packages.schemas.config.api import ApiClientConfig


class BaseHttpClient:
    """
    설정 주입이 가능한 범용 비동기 HTTP 클라이언트.
    - Rate Limit, 재시도 정책을 외부에서 설정 가능
    """

    def __init__(self, config: ApiClientConfig):
        self._session = None

        self._limiter = AsyncLimiter(config.rate_limit.max_rate, config.rate_limit.time_period)

        self._retryer = AsyncRetrying(
            stop=stop_after_attempt(config.retry.attempts),
            wait=wait_random(min=config.retry.wait_min_s, max=config.retry.wait_max_s),
            retry=retry_if_exception_type((aiohttp.ClientError, ValueError)),
            reraise=True,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        유효한 세션을 가져오거나, 없으면 새로 생성합니다.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def __aenter__(self):
        await self._get_session()  # with 진입 시 세션이 준비되도록 보장
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _perform_request(self, method: str, url: str, expect_json: bool = True, **kwargs) -> dict | list | str:
        """실제 HTTP 요청을 보내는 내부 메소드. Rate Limit이 여기에 적용됩니다."""
        async with self._limiter:
            async with self._session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                if not expect_json:
                    return await response.text()
                data = await response.json()
                content = data.get("content")
                return content if content is not None else data

    async def request(self, *args, **kwargs):
        """외부에 노출되는 공개 메소드. 재시도 로직이 여기에 적용됩니다."""
        return await self._retryer(self._perform_request, *args, **kwargs)

    async def close(self):
        """세션을 안전하게 닫습니다."""
        if self._session and not self._session.closed:
            await self._session.close()
