from unittest.mock import AsyncMock

import aiohttp
import pytest

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkApiClient
from chatzzk.packages.schemas.config.api import ChzzkApiConfig


@pytest.fixture
def test_chzzk_api_config() -> ChzzkApiConfig:
    # 테스트에 필요한 값으로 실제 ChzzkApiConfig 객체를 생성
    return ChzzkApiConfig(
        channel_info_template="http://mock.api/channel/{channel_id}",
        channel_vods_info_template="http://mock.api/channel/{channel_id}/vods?page={page_idx}",
        vod_info_template="http://mock.api/vod/{video_no}",
        vod_chats_template="http://mock.api/vod/{video_no}/chats",
        vod_url_template="http://mock.api/vod/{video_id}/manifest?in_key={in_key}",
        vod_manifest_headers={"X-Custom-Header": "test"},
        https_proxy="http://mock.proxy:8080",
    )


@pytest.fixture
def mock_http_client():
    """
    Fixture to provide a mocked BaseHttpClient instance.
    This allows testing ChzzkApiClient's interaction with its HTTP client dependency
    without making actual network requests.
    """
    return AsyncMock(spec=BaseHttpClient)


@pytest.fixture
def chzzk_api_client(mock_http_client, test_chzzk_api_config):
    """
    Fixture to provide an instance of ChzzkApiClient with a mocked BaseHttpClient.
    """
    return ChzzkApiClient(mock_http_client, test_chzzk_api_config)


# --- Tests for get_channel_info ---


@pytest.mark.asyncio
async def test_get_channel_info_success(chzzk_api_client, mock_http_client):
    """
    목적: get_channel_info가 성공적인 API 응답을 올바르게 처리하는지 테스트합니다.
    """
    channel_id = "test_channel_id"
    mock_response_content = {"channelId": channel_id, "channelName": "Test Channel"}
    mock_http_client.get.return_value = mock_response_content

    result = await chzzk_api_client.get_channel_info(channel_id)

    mock_http_client.get.assert_called_once_with(f"http://mock.api/channel/{channel_id}")
    assert result == mock_response_content


@pytest.mark.asyncio
async def test_get_channel_info_not_found(chzzk_api_client, mock_http_client):
    """
    목적: get_channel_info가 404 Not Found 에러 발생 시 None을 반환하는지 테스트합니다.
    """
    channel_id = "not_found_channel"
    mock_http_client.get.side_effect = aiohttp.ClientResponseError(
        request_info=None, history=None, status=404, message="Not Found"
    )

    result = await chzzk_api_client.get_channel_info(channel_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_channel_info_server_error(chzzk_api_client, mock_http_client):
    """
    목적: get_channel_info가 500 서버 에러 발생 시 예외를 그대로 raise하는지 테스트합니다.
    """
    channel_id = "server_error_channel"
    mock_http_client.get.side_effect = aiohttp.ClientResponseError(
        request_info=None, history=None, status=500, message="Server Error"
    )

    with pytest.raises(aiohttp.ClientResponseError) as excinfo:
        await chzzk_api_client.get_channel_info(channel_id)
    assert excinfo.value.status == 500


@pytest.mark.asyncio
async def test_get_channel_info_network_error(chzzk_api_client, mock_http_client):
    """
    목적: get_channel_info가 네트워크 에러(ClientError) 발생 시 예외를 raise하는지 테스트합니다.
    """
    channel_id = "network_error_channel"
    mock_http_client.get.side_effect = aiohttp.ClientError("Mock Network Error")

    with pytest.raises(aiohttp.ClientError):
        await chzzk_api_client.get_channel_info(channel_id)


# --- Tests for get_channel_vods_info ---


@pytest.mark.asyncio
async def test_get_channel_vods_info_success(chzzk_api_client, mock_http_client):
    """
    목적: get_channel_vods_info가 성공적인 API 응답을 올바르게 처리하는지 테스트합니다.
    """
    channel_id = "test_channel_id"
    page_idx = 1
    expected_url = f"http://mock.api/channel/{channel_id}/vods?page={page_idx}"
    mock_response_content = {"data": [{"videoNo": "123"}], "page": page_idx}
    mock_http_client.get.return_value = mock_response_content

    result = await chzzk_api_client.get_channel_vods_info(channel_id, page_idx)

    mock_http_client.get.assert_called_once_with(expected_url)
    assert result == mock_response_content


@pytest.mark.asyncio
async def test_get_channel_vods_info_not_found(chzzk_api_client, mock_http_client):
    """
    목적: get_channel_vods_info가 404 에러 발생 시 None을 반환하는지 테스트합니다.
    """
    mock_http_client.get.side_effect = aiohttp.ClientResponseError(
        request_info=None, history=None, status=404, message="Not Found"
    )
    result = await chzzk_api_client.get_channel_vods_info("test_id", 1)
    assert result is None


# --- Tests for get_vod_info ---


@pytest.mark.asyncio
async def test_get_vod_info_success(chzzk_api_client, mock_http_client):
    """
    목적: get_vod_info가 성공적인 API 응답을 올바르게 처리하는지 테스트합니다.
    """
    video_no = "test_video_no"
    expected_url = f"http://mock.api/vod/{video_no}"
    mock_response_content = {"videoNo": video_no, "videoTitle": "Test VOD"}
    mock_http_client.get.return_value = mock_response_content

    result = await chzzk_api_client.get_vod_info(video_no)

    mock_http_client.get.assert_called_once_with(expected_url)
    assert result == mock_response_content


@pytest.mark.asyncio
async def test_get_vod_info_server_error(chzzk_api_client, mock_http_client):
    """
    목적: get_vod_info가 500 서버 에러 발생 시 예외를 raise하는지 테스트합니다.
    """
    mock_http_client.get.side_effect = aiohttp.ClientResponseError(
        request_info=None, history=None, status=500, message="Server Error"
    )
    with pytest.raises(aiohttp.ClientResponseError):
        await chzzk_api_client.get_vod_info("test_video_no")


# --- Tests for get_vod_chats ---


@pytest.mark.asyncio
async def test_get_vod_chats_success(chzzk_api_client, mock_http_client):
    """
    목적: get_vod_chats가 성공적인 API 응답을 올바르게 처리하는지 테스트합니다.
    """
    video_no = "test_video_no"
    next_player_message_time_ms = 1000
    expected_url = f"http://mock.api/vod/{video_no}/chats"
    mock_response_content = {"videoChats": [{"message": "hello"}], "nextPlayerMessageTime": 2000}
    mock_http_client.get.return_value = mock_response_content

    result = await chzzk_api_client.get_vod_chats(video_no, next_player_message_time_ms)

    mock_http_client.get.assert_called_once_with(
        expected_url, params={"playerMessageTime": next_player_message_time_ms}
    )
    assert result == mock_response_content


@pytest.mark.asyncio
async def test_get_vod_chats_network_error(chzzk_api_client, mock_http_client):
    """
    목적: get_vod_chats가 네트워크 에러 발생 시 예외를 raise하는지 테스트합니다.
    """
    mock_http_client.get.side_effect = aiohttp.ClientError("Network Error")
    with pytest.raises(aiohttp.ClientError):
        await chzzk_api_client.get_vod_chats("test_video_no", 1000)


# --- Tests for get_vod_manifest ---


@pytest.mark.asyncio
async def test_get_vod_manifest_success(chzzk_api_client, mock_http_client, test_chzzk_api_config):
    """
    목적: get_vod_manifest가 성공적인 API 응답을 올바르게 처리하는지 테스트합니다.
    """
    video_id = "test_video_id"
    in_key = "test_in_key"
    expected_url = f"http://mock.api/vod/{video_id}/manifest?in_key={in_key}"
    mock_response_content = "#EXTM3U\n#EXT-X-VERSION:3\n..."
    mock_http_client.get.return_value = mock_response_content

    result = await chzzk_api_client.get_vod_manifest(video_id, in_key)

    mock_http_client.get.assert_called_once_with(
        expected_url,
        expect_json=False,
        proxy=test_chzzk_api_config.https_proxy,
        headers=test_chzzk_api_config.vod_manifest_headers,
    )
    assert result == mock_response_content


@pytest.mark.asyncio
async def test_get_vod_manifest_not_found(chzzk_api_client, mock_http_client):
    """
    목적: get_vod_manifest가 404 에러 발생 시 None을 반환하는지 테스트합니다.
    """
    mock_http_client.get.side_effect = aiohttp.ClientResponseError(
        request_info=None, history=None, status=404, message="Not Found"
    )
    result = await chzzk_api_client.get_vod_manifest("test_video_id", "test_in_key")
    assert result is None


@pytest.mark.asyncio
async def test_get_vod_manifest_server_error(chzzk_api_client, mock_http_client):
    """
    목적: get_vod_manifest가 500 서버 에러 발생 시 예외를 raise하는지 테스트합니다.
    """
    mock_http_client.get.side_effect = aiohttp.ClientResponseError(
        request_info=None, history=None, status=500, message="Server Error"
    )
    with pytest.raises(aiohttp.ClientResponseError) as excinfo:
        await chzzk_api_client.get_vod_manifest("test_video_id", "test_in_key")
    assert excinfo.value.status == 500
