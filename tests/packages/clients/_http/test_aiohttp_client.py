import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import aiohttp
import pytest
from loguru import logger

from chatzzk.packages.clients._http.aiohttp_client import AioHTTPClient
from chatzzk.packages.schemas.config.clients.http import AioHTTPConfig


@pytest.fixture
def mock_config():
    """Provides a mock AioHTTPClientConfig."""
    return AioHTTPConfig(
        timeout_s=1,
        retry_attempts=3,
        retry_wait_min_s=1,
        retry_wait_max_s=2,
    )


@pytest.fixture
def mock_session():
    """Provides a mock aiohttp.ClientSession."""
    # specing ClientSession will make its request method have the correct signature
    return MagicMock(spec=aiohttp.ClientSession)


@pytest.fixture
def http_client(mock_session, mock_config):
    """Provides an AioHTTPClient instance with a mock session."""
    return AioHTTPClient(session=mock_session, config=mock_config)


@pytest.mark.asyncio
async def test_get_json_response(http_client, mock_session):
    """Tests a successful GET request with a JSON response."""
    url = "http://test.com/json"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content_type = "application/json"
    mock_response.json = AsyncMock(return_value={"key": "value"})
    mock_response.raise_for_status = MagicMock()

    mock_session.request.return_value.__aenter__.return_value = mock_response

    async with http_client.get(url) as response:
        result = await response.json()

    mock_session.request.assert_called_once_with("GET", url, timeout=ANY)
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_get_text_response(http_client, mock_session):
    """Tests a successful GET request with a text response."""
    url = "http://test.com/text"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content_type = "text/plain"
    mock_response.text = AsyncMock(return_value="plain text")
    mock_response.raise_for_status = MagicMock()

    mock_session.request.return_value.__aenter__.return_value = mock_response

    async with http_client.get(url) as response:
        result = await response.text()

    mock_session.request.assert_called_once_with("GET", url, timeout=ANY)
    assert result == "plain text"


@pytest.mark.asyncio
async def test_post_request(http_client, mock_session):
    """Tests a successful POST request."""
    url = "http://test.com/post"
    post_data = {"data": "content"}
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content_type = "application/json"
    mock_response.json = AsyncMock(return_value={"status": "ok"})
    mock_response.raise_for_status = MagicMock()

    mock_session.request.return_value.__aenter__.return_value = mock_response

    async with http_client.post(url, json=post_data) as response:
        result = await response.json()

    mock_session.request.assert_called_once_with("POST", url, timeout=ANY, json=post_data)
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_retry_on_client_error(http_client, mock_session, mock_config):
    """Tests if the client retries on aiohttp.ClientError."""
    url = "http://test.com/retry"

    # 1️⃣ mock side_effect 설정 — 요청할 때마다 같은 예외를 발생시킴
    mock_session.request.side_effect = aiohttp.ClientError("Connection failed")

    with pytest.raises(aiohttp.ClientError):
        async with http_client.get(url):
            pass

    # 재시도 횟수 검증
    assert mock_session.request.call_count == mock_config.retry_attempts


@pytest.mark.asyncio
async def test_retry_on_timeout_error(http_client, mock_session, mock_config):
    """Tests if the client retries on asyncio.TimeoutError."""
    url = "http://test.com/timeout"
    mock_session.request.side_effect = TimeoutError("Request timed out")

    with pytest.raises(asyncio.TimeoutError):
        async with http_client.get(url):
            pass

    assert mock_session.request.call_count == mock_config.retry_attempts


# 가능성이 낮기 때문에 우선순위 낮음 추후 점검
# @pytest.mark.asyncio
# async def test_http_error_no_retry(http_client, mock_session):
#     """Tests that ClientResponseError is not retried."""
#     url = "http://test.com/notfound"
#     mock_response = AsyncMock()
#     mock_response.status = 404

#     # We need to mock raise_for_status as a sync function
#     mock_response.raise_for_status = MagicMock(
#         side_effect=aiohttp.ClientResponseError(
#             request_info=MagicMock(),
#             history=(),
#             status=404,
#             message="Not Found",
#         )
#     )

#     mock_session.request.return_value.__aenter__.return_value = mock_response

#     with pytest.raises(aiohttp.ClientResponseError):
#         async with http_client.get(url):
#             pass

#     assert mock_session.request.call_count == 1


@pytest.mark.asyncio
async def test_unexpected_error_no_retry(http_client, mock_session):
    """Tests that an unexpected error is not retried."""
    url = "http://test.com/unexpected"
    mock_session.request.side_effect = ValueError("An unexpected error")

    with pytest.raises(ValueError):
        async with http_client.get(url):
            pass

    assert mock_session.request.call_count == 1


@pytest.mark.asyncio
async def test_before_sleep_log(mock_config):
    """Tests the logging callback before a retry."""
    client = AioHTTPClient(session=MagicMock(), config=mock_config)

    # Create a mock retry_state object
    mock_outcome = MagicMock()
    mock_outcome.exception.return_value = aiohttp.ClientError("Test Exception")

    mock_retry_state = MagicMock()
    mock_retry_state.outcome = mock_outcome
    mock_retry_state.attempt_number = 2

    with patch.object(logger, "warning") as mock_log_warning:
        client._before_sleep_log(mock_retry_state)
        mock_log_warning.assert_called_once_with(
            "Retrying request due to ClientError: Test Exception. This is attempt 2."
        )
