import aiohttp
import pytest
from aioresponses import CallbackResult, aioresponses

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.schemas.config.api import BaseHttpConfig, RateLimitConfig, RetryConfig


@pytest.fixture
def mock_base_http_config() -> BaseHttpConfig:
    """
    목적: 테스트에 사용될 `BaseHttpConfig` 객체를 생성합니다.
    """
    return BaseHttpConfig(
        rate_limit=RateLimitConfig(max_rate=10, time_period=1),
        retry=RetryConfig(attempts=3, wait_min_s=1, wait_max_s=2),
    )


@pytest.mark.asyncio
async def test_successful_get_request(mock_base_http_config):
    """
    목적: BaseHttpClient가 성공적인 GET 요청을 올바르게 처리하는지 테스트합니다.
    """
    async with BaseHttpClient(mock_base_http_config) as client:
        with aioresponses() as m:
            m.get("http://test.com/data", status=200, payload={"key": "value"})
            response = await client.get("http://test.com/data")
            assert response == {"key": "value"}


@pytest.mark.asyncio
async def test_successful_post_request(mock_base_http_config):
    """
    목적: 새로 추가된 post 메소드가 성공적인 POST 요청을 올바르게 처리하는지 테스트합니다.
    """
    async with BaseHttpClient(mock_base_http_config) as client:
        with aioresponses() as m:
            m.post("http://test.com/data", status=200, payload={"status": "created"})
            response = await client.post("http://test.com/data", json={"key": "value"})
            assert response == {"status": "created"}


@pytest.mark.asyncio
async def test_successful_text_request(mock_base_http_config):
    """
    목적: BaseHttpClient가 JSON이 아닌 일반 텍스트 응답을 올바르게 처리하는지 테스트합니다.
    내용: `expect_json=False` 옵션을 사용하여 `client.get()`을 호출했을 때,
          HTTP 응답의 body를 텍스트 그대로 반환하는지 확인합니다.
    """
    async with BaseHttpClient(mock_base_http_config) as client:
        with aioresponses() as m:
            m.get("http://test.com/text", status=200, body="Hello, world!")
            response = await client.get("http://test.com/text", expect_json=False)
            assert response == "Hello, world!"


@pytest.mark.asyncio
async def test_get_retry_on_failure_then_succeed(mock_base_http_config):
    """
    목적: GET 요청이 실패했을 때, 재시도 로직이 정상 동작하여 결국 성공하는지 테스트합니다.
    """
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return CallbackResult(status=503, reason="Service Unavailable")
        return CallbackResult(status=200, payload={"status": "ok"})

    async with BaseHttpClient(mock_base_http_config) as client:
        with aioresponses() as m:
            m.get("http://test.com/retry", callback=retry_callback, repeat=True)
            response = await client.get("http://test.com/retry")
            assert response == {"status": "ok"}
            assert call_count == 3


@pytest.mark.asyncio
async def test_post_retry_on_failure_then_succeed(mock_base_http_config):
    """
    목적: POST 요청이 실패했을 때, 재시도 로직이 정상 동작하여 결국 성공하는지 테스트합니다.
    """
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return CallbackResult(status=503, reason="Service Unavailable")
        return CallbackResult(status=200, payload={"status": "ok"})

    async with BaseHttpClient(mock_base_http_config) as client:
        with aioresponses() as m:
            m.post("http://test.com/retry", callback=retry_callback, repeat=True)
            response = await client.post("http://test.com/retry", json={})
            assert response == {"status": "ok"}
            assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted(mock_base_http_config):
    """
    목적: 설정된 재시도 횟수를 모두 소진했을 때, 마지막 예외를 발생시키는지 테스트합니다.
    """
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return CallbackResult(status=503, reason="Service Unavailable")

    async with BaseHttpClient(mock_base_http_config) as client:
        with aioresponses() as m:
            m.get("http://test.com/fail", callback=retry_callback, repeat=True)
            with pytest.raises(aiohttp.ClientResponseError) as excinfo:
                await client.get("http://test.com/fail")
            assert excinfo.value.status == 503
            assert call_count == 3


@pytest.mark.asyncio
async def test_context_manager_closes_session(mock_base_http_config):
    """
    목적: 'async with' 컨텍스트 관리자가 BaseHttpClient의 세션을 올바르게 관리하는지 테스트합니다.
    내용: 컨텍스트에 진입하면 세션이 생성되고, 컨텍스트를 빠져나가면 세션이 자동으로
          닫히는지(`_session.closed == True`) 확인하여 리소스 누수를 방지합니다.
    """
    client = BaseHttpClient(mock_base_http_config)
    assert client._session is None

    async with client:
        assert client._session is not None
        assert not client._session.closed

    assert client._session.closed
