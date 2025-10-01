import aiohttp
import pytest
from aioresponses import CallbackResult, aioresponses

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.schemas.config.api import (
    ApiClientConfig,
    BaseHttpConfig,
    ChzzkApiConfig,
    RateLimitConfig,
    RetryConfig,
)


@pytest.fixture
def mock_api_client_config() -> ApiClientConfig:
    """
    목적: 테스트에 사용될 `ApiClientConfig` 객체를 생성합니다.
    내용: `BaseHttpConfig`와 `ChzzkApiConfig`를 포함하는 전체 API 클라이언트 설정을
          테스트용 값으로 초기화하여 반환합니다.
    """
    mock_chzzk_api_config = ChzzkApiConfig(
        channel_info_template="http://mock.chzzk.api/channels/{channel_id}",
        channel_vods_info_template="http://mock.chzzk.api/channels/{channel_id}/videos",
        vod_info_template="http://mock.chzzk.api/videos/{video_no}",
        vod_chats_template="http://mock.chzzk.api/videos/{video_no}/chats",
        vod_url_template="http://mock.chzzk.api/playback/{video_id}?key={in_key}",
    )

    mock_base_http_config = BaseHttpConfig(
        rate_limit=RateLimitConfig(max_rate=10, time_period=1),
        retry=RetryConfig(attempts=3, wait_min_s=1, wait_max_s=2),
    )

    return ApiClientConfig(
        base_http=mock_base_http_config,
        chzzk_api=mock_chzzk_api_config,
    )


@pytest.mark.asyncio
async def test_successful_json_request(mock_api_client_config):
    """
    목적: BaseHttpClient가 성공적인 JSON GET 요청을 올바르게 처리하는지 테스트합니다.
    내용: 200 OK 상태와 JSON 페이로드를 반환하는 mock API에 대해 `client.get()`을 호출하고,
          반환된 데이터가 예상과 일치하는지 확인합니다.
    """
    async with BaseHttpClient(mock_api_client_config.base_http) as client:
        with aioresponses() as m:
            m.get("http://test.com/data", status=200, payload={"key": "value"})
            response = await client.get("http://test.com/data")
            assert response == {"key": "value"}


@pytest.mark.asyncio
async def test_successful_json_with_content_key(mock_api_client_config):
    """
    목적: API 응답이 'content' 키로 래핑된 특정 JSON 구조를 올바르게 파싱하는지 테스트합니다.
    내용: 'content' 키를 포함하는 mock 응답을 설정하고, `client.get()`이 'content' 내부의
          객체를 직접 반환하는지 확인합니다. 이는 API 응답 규칙을 준수하는지 검증합니다.
    """
    async with BaseHttpClient(mock_api_client_config.base_http) as client:
        with aioresponses() as m:
            m.get("http://test.com/data", status=200, payload={"content": {"nested_key": "nested_value"}})
            response = await client.get("http://test.com/data")
            assert response == {"nested_key": "nested_value"}


@pytest.mark.asyncio
async def test_successful_text_request(mock_api_client_config):
    """
    목적: BaseHttpClient가 JSON이 아닌 일반 텍스트 응답을 올바르게 처리하는지 테스트합니다.
    내용: `expect_json=False` 옵션을 사용하여 `client.get()`을 호출했을 때,
          HTTP 응답의 body를 텍스트 그대로 반환하는지 확인합니다.
    """
    async with BaseHttpClient(mock_api_client_config.base_http) as client:
        with aioresponses() as m:
            m.get("http://test.com/text", status=200, body="Hello, world!")
            response = await client.get("http://test.com/text", expect_json=False)
            assert response == "Hello, world!"


@pytest.mark.asyncio
async def test_retry_on_failure_then_succeed(mock_api_client_config):
    """
    목적: 서버 오류 발생 시, 재시도 로직이 정상 동작하여 결국 성공하는지 테스트합니다.
    내용: aioresponses의 callback을 사용하여 처음 2번은 503 오류를, 3번째 호출에서는 200 성공을
          반환하도록 설정합니다. 클라이언트가 3번의 시도 끝에 성공적으로 데이터를 받아오는지,
          총 호출 횟수가 3번인지 확인합니다.
    """
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return CallbackResult(status=503, reason="Service Unavailable")
        return CallbackResult(status=200, payload={"status": "ok"})

    async with BaseHttpClient(mock_api_client_config.base_http) as client:
        with aioresponses() as m:
            m.get("http://test.com/retry", callback=retry_callback, repeat=True)
            response = await client.get("http://test.com/retry")
            assert response == {"status": "ok"}
            assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted(mock_api_client_config):
    """
    목적: 설정된 재시도 횟수를 모두 소진했을 때, 마지막 예외를 발생시키는지 테스트합니다.
    내용: 모든 요청에 503 오류를 반환하도록 mock API를 설정합니다. `RetryConfig`에 설정된
          재시도 횟수(3번)만큼 요청이 발생하고, 그 이후 `aiohttp.ClientResponseError` 예외가
          발생하는지 확인합니다.
    """
    call_count = 0

    def retry_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        return CallbackResult(status=503, reason="Service Unavailable")

    # The fixture sets attempts to 3
    async with BaseHttpClient(mock_api_client_config.base_http) as client:
        with aioresponses() as m:
            m.get("http://test.com/fail", callback=retry_callback, repeat=True)

            with pytest.raises(aiohttp.ClientResponseError) as excinfo:
                await client.get("http://test.com/fail")

            # tenacity가 재시도 후 마지막 예외를 다시 발생시키는지 확인
            assert excinfo.value.status == 503
            # 총 3번 호출되었는지 확인 (설정된 attempts 수와 동일)
            assert call_count == 3


@pytest.mark.asyncio
async def test_context_manager_closes_session(mock_api_client_config):
    """
    목적: 'async with' 컨텍스트 관리자가 BaseHttpClient의 세션을 올바르게 관리하는지 테스트합니다.
    내용: 컨텍스트에 진입하면 세션이 생성되고, 컨텍스트를 빠져나가면 세션이 자동으로
          닫히는지(`_session.closed == True`) 확인합니다.
    """
    client = BaseHttpClient(mock_api_client_config.base_http)
    assert client._session is None

    async with client:
        assert client._session is not None
        assert not client._session.closed

    assert client._session.closed
