from unittest.mock import AsyncMock, MagicMock

import pytest

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.clients.chzzk import ChannelInfo
from chatzzk.services.service_implementations.management.chzzk_channel_management_service import (
    ChzzkChannelManagementService,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_repos():
    """서비스에 주입될 Mock 객체들을 생성하는 Fixture"""
    return {
        "db_session_factory": AsyncMock(),
        "platform_repo": AsyncMock(),
        "channel_repo": AsyncMock(),
        "chzzk_api_client": AsyncMock(),
    }


async def test_add_channel_when_channel_exists(mock_repos):
    """
    add_channel 호출 시 채널이 이미 존재할 경우, create 로직을 타지 않고
    기존 채널의 ID를 반환하는지 테스트합니다.
    """
    # given
    # 1. 'async with ... as session' 구문 이후에 사용될 가짜 session 객체를 만듭니다.
    mock_session = AsyncMock()

    mock_transaction = AsyncMock()
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=mock_transaction)

    session_context_manager = AsyncMock()
    session_context_manager.__aenter__.return_value = mock_session

    mock_repos["db_session_factory"] = MagicMock(return_value=session_context_manager)
    find_by_code_mock = AsyncMock()
    mock_repos["platform_repo"].find_by_code.return_value = find_by_code_mock

    mock_repos["channel_repo"].find_by_platform_channel_id.return_value = MagicMock(id=123)

    service = ChzzkChannelManagementService(**mock_repos)

    # when
    result_id = await service.add_channel(PlatformCode.CHZZK.value, "existing_id")

    # then
    # 1. find_by_platform_channel_id가 올바른 session 객체와 함께 호출되었는지 확인
    mock_repos["channel_repo"].find_by_platform_channel_id.assert_awaited_once_with(
        mock_session, find_by_code_mock, "existing_id"
    )

    # 2. 외부 API와 create 메서드가 호출되지 않았는지 확인
    mock_repos["chzzk_api_client"].fetch_channel_info.assert_not_awaited()
    mock_repos["channel_repo"].create.assert_not_awaited()

    # 3. 기존 채널의 ID가 반환되었는지 확인
    assert result_id == 123


async def test_add_channel_when_new_channel(mock_repos):
    """
    add_channel 호출 시 새로운 채널일 경우, 외부 API 조회 및 create 로직을
    정상적으로 수행하는지 테스트합니다.
    """
    mock_session = AsyncMock()

    mock_transaction = AsyncMock()
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=mock_transaction)

    session_context_manager = AsyncMock()
    session_context_manager.__aenter__.return_value = mock_session
    mock_repos["db_session_factory"] = MagicMock(return_value=session_context_manager)
    # given
    # 처음에는 채널이 존재하지 않음 (None 반환)
    mock_repos["channel_repo"].find_by_platform_channel_id.return_value = None

    # 외부 API는 가짜 채널 정보를 반환
    fake_channel_info = ChannelInfo(
        channel_id="new_chzzk_id",
        channel_name="새로운 채널",
        verified_mark=True,
        channel_image_url="fake_image_url",
        follower_count=3,
        open_live=False,
        subscription_availability=False,
    )
    mock_repos["chzzk_api_client"].fetch_channel_info.return_value = fake_channel_info

    # create 메서드는 ID 999를 가진 객체를 반환
    mock_repos["channel_repo"].create.return_value = MagicMock(id=999)

    service = ChzzkChannelManagementService(**mock_repos)

    # when
    result_id = await service.add_channel(PlatformCode.CHZZK.value, "new_chzzk_id")

    # then
    # 1. find 메서드들이 정상적으로 호출되었는지 확인
    mock_repos["platform_repo"].find_by_code.assert_awaited_once()
    mock_repos["channel_repo"].find_by_platform_channel_id.assert_awaited_once()

    # 2. 외부 API와 create 메서드가 정상적으로 호출되었는지 확인
    mock_repos["chzzk_api_client"].fetch_channel_info.assert_awaited_once_with("new_chzzk_id")
    mock_repos["channel_repo"].create.assert_awaited_once()

    # 3. 새로 생성된 채널의 ID가 반환되었는지 확인
    assert result_id == 999
