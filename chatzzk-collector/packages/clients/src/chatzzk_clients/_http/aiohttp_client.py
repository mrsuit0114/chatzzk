import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
from loguru import logger
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from chatzzk_core.schemas.config.clients.http import AioHTTPConfig


class AioHTTPClient:
    def __init__(self, config: AioHTTPConfig, session: aiohttp.ClientSession):
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=config.timeout_s)

        self._retryer = AsyncRetrying(
            stop=stop_after_attempt(config.retry_attempts),
            wait=wait_exponential(
                min=config.retry_wait_min_s, max=config.retry_wait_max_s, multiplier=config.multiplier
            ),
            retry=retry_if_exception_type(self._is_retryable_exception),
            reraise=True,
            before_sleep=self._before_sleep_log,
        )

    @staticmethod
    def _is_retryable_exception(exception: BaseException) -> bool:
        """
        재시도할 예외인지 판단하는 로직
        - TimeoutError: 무조건 재시도
        - ClientResponseError: 5xx 서버 에러만 재시도 (4xx는 클라이언트 잘못이므로 재시도 X)
        - ClientError: 그 외 연결 끊김 등 네트워크 에러는 재시도
        """
        if isinstance(exception, asyncio.TimeoutError):
            return True

        if isinstance(exception, aiohttp.ClientResponseError):
            # 500번대 에러(서버 장애)만 재시도
            return 500 <= exception.status < 600

        if isinstance(exception, aiohttp.ClientError):
            # DNS 실패, 연결 거부 등 네트워크 레벨 에러
            return True

        return False

    @staticmethod
    def _before_sleep_log(retry_state):
        """재시도하기 전에 로그를 남기는 콜백 함수"""
        exception = retry_state.outcome.exception()
        logger.warning(
            f"Retrying request due to {exception.__class__.__name__}: {exception}. "
            f"This is attempt {retry_state.attempt_number}."
        )

    @asynccontextmanager
    async def _request(self, method: str, url: str, **kwargs: Any):
        try:
            async for attempt in self._retryer:
                with attempt:
                    try:
                        async with self._session.request(method, url, timeout=self._timeout, **kwargs) as response:
                            response.raise_for_status()
                            yield response
                            return

                    except (TimeoutError, aiohttp.ClientError) as e:
                        if attempt.retry_state.attempt_number < self._retryer.stop.max_attempt_number:
                            # 마지막 시도가 아닐 때만 로그 (마지막은 error 로그가 처리 or 상위 전파)
                            logger.warning(f"Request failed (Attempt {attempt.retry_state.attempt_number}): {e}")
                        raise

        except (TimeoutError, aiohttp.ClientError) as e:
            # 모든 재시도 후 최종 실패
            logger.error(f"Request permanently failed for url {url}: {e}")
            raise

    def get(self, url: str, **kwargs: Any) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        return self._request("POST", url, **kwargs)
