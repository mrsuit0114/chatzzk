import asyncio
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
from loguru import logger
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from chatzzk.packages.schemas.config.clients.http import AioHTTPConfig


class AioHTTPClient:
    def __init__(self, config: AioHTTPConfig, session: aiohttp.ClientSession):
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=config.timeout_s)

        # 멀티 쓰레딩으로 요청할 때 서버 api limit을 고려할 것
        self._retryer = AsyncRetrying(
            stop=stop_after_attempt(config.retry_attempts),
            wait=wait_exponential(
                min=config.retry_wait_min_s, max=config.retry_wait_max_s, multiplier=config.multiplier
            ),
            retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
            reraise=True,
            before_sleep=self._before_sleep_log,
        )

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
                        logger.warning(f"[{attempt.retry_state.attempt_number}] Request failed: {e}")
                        raise

        except (TimeoutError, aiohttp.ClientError) as e:
            # 모든 재시도 후 최종 실패
            logger.error(f"Request permanently failed for url {url}: {e}")
            raise

    def get(self, url: str, **kwargs: Any):
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any):
        return self._request("POST", url, **kwargs)
