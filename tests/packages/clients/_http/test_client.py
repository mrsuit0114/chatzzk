from unittest.mock import MagicMock

import pytest
from aioresponses import CallbackResult, aioresponses

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.schemas.config.api import ApiClientConfig, RateLimitConfig, RetryConfig

# Assuming the global settings object is imported like this in BaseHttpClient:
# from chatzzk.packages.schemas.config.settings import settings as global_settings_instance


@pytest.fixture
def mock_api_client_config() -> ApiClientConfig:
    """테스트용 ApiClientConfig 객체를 생성합니다."""
    return ApiClientConfig(
        base_url="http://test.com",
        rate_limit=RateLimitConfig(max_rate=10, time_period=1),
        retry=RetryConfig(attempts=5, wait_min_s=1, wait_max_s=2),
    )


@pytest.fixture
def mock_settings(mocker, mock_api_client_config):
    """전역 settings 객체를 모킹합니다."""
    mock_settings_instance = MagicMock()
    mock_settings_instance.api = mock_api_client_config
    mocker.patch("chatzzk.packages.clients._http.client.settings", new=mock_settings_instance)
    return mock_settings_instance


@pytest.mark.asyncio
async def test_successful_json_request(mock_settings):
    """성공적인 JSON GET 요청을 테스트합니다."""
    async with BaseHttpClient() as client:
        with aioresponses() as m:
            m.get("http://test.com/data", status=200, payload={"key": "value"})
            response = await client.request("GET", "http://test.com/data")
            assert response == {"key": "value"}


@pytest.mark.asyncio
async def test_successful_json_with_content_key(mock_settings):
    """'content' 키를 포함하는 특정 JSON 응답 구조를 테스트합니다."""
    async with BaseHttpClient() as client:
        with aioresponses() as m:
            m.get("http://test.com/data", status=200, payload={"content": {"nested_key": "nested_value"}})
            response = await client.request("GET", "http://test.com/data")
            assert response == {"nested_key": "nested_value"}


@pytest.mark.asyncio
async def test_successful_text_request(mock_settings):
    """성공적인 일반 텍스트 GET 요청을 테스트합니다."""
    async with BaseHttpClient() as client:
        with aioresponses() as m:
            m.get("http://test.com/text", status=200, body="Hello, world!")
            response = await client.request("GET", "http://test.com/text", expect_json=False)
            assert response == "Hello, world!"


@pytest.mark.asyncio
async def test_retry_on_failure_then_succeed(mock_settings):
    """서버 오류 후 재시도하여 성공하는 경우를 테스트합니다. (callback 사용)"""
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return CallbackResult(status=503, reason="Service Unavailable")
        return CallbackResult(status=200, payload={"status": "ok"})

    async with BaseHttpClient() as client:
        with aioresponses() as m:
            m.get("http://test.com/retry", callback=retry_callback, repeat=True)
            response = await client.request("GET", "http://test.com/retry")
            assert response == {"status": "ok"}
            assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted(mock_settings):
    """모든 재시도가 실패하여 예외가 발생하는 경우를 테스트합니다. (callback 사용)"""
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return CallbackResult(status=503, reason="Service Unavailable")

    # 재시도 횟수를 3으로 설정
    # mock_settings.api_client_config.retry.attempts = 3 # This would modify the fixture, better to set it in the fixture itself if needed
    # For this test, we need to ensure the mock_api_client_config used by mock_settings has attempts=3
    # Let's modify mock_api_client_config for this specific test if needed, or ensure default is 3
    # The default is 5, so we need to override it for this test.
    mock_settings.api.retry.attempts = 3

    async with BaseHttpClient() as client:
        with aioresponses() as m:
            m.get("http://test.com/fail", callback=retry_callback, repeat=True)

            with pytest.raises(Exception) as excinfo:
                await client.request("GET", "http://test.com/fail")

            # tenacity가 재시도 후 마지막 예외를 다시 발생시키는지 확인
            assert "503" in str(excinfo.value)
            # 총 3번 호출되었는지 확인
            assert call_count == 3


@pytest.mark.asyncio
async def test_context_manager_closes_session(mock_settings):
    """컨텍스트 관리자(async with)가 세션을 올바르게 닫는지 테스트합니다."""
    client = BaseHttpClient()
    assert client._session is None

    async with client:
        assert client._session is not None
        assert not client._session.closed

    assert client._session.closed
