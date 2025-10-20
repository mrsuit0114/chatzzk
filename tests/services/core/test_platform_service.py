from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.services.service_implementations.core.platform_service import PlatformService

pytestmark = pytest.mark.asyncio


async def test_add_platform_when_not_existing():
    """플랫폼이 존재하지 않을 때, repository의 create를 호출하는지 테스트"""
    # given
    mock_repo = AsyncMock()
    mock_repo.find_by_code.return_value = None
    mock_repo.create.return_value = SimpleNamespace(id=1)

    mock_transaction = AsyncMock()
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=mock_transaction)

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    service = PlatformService(db_session_factory=mock_session_factory, platform_repo=mock_repo)

    # when
    result = await service.add_platform(PlatformCode.CHZZK, "치지직", "치즈")

    # then
    # begin 메서드가 호출되었는지 확인
    mock_session.begin.assert_called_once()

    # find_by_code가 올바른 인자와 함께 호출되었는지 확인
    mock_repo.find_by_code.assert_awaited_once_with(mock_session, PlatformCode.CHZZK)

    # create가 올바른 인자와 함께 호출되었는지 확인
    mock_repo.create.assert_awaited_once_with(mock_session, ANY)
    called_dto = mock_repo.create.call_args[0][1]

    # 반환된 ID가 올바른지 확인
    assert result == 1
    assert called_dto.platform_code == PlatformCode.CHZZK
    assert called_dto.platform_name == "치지직"
    assert called_dto.donation_unit == "치즈"


async def test_add_platform_when_existing():
    """플랫폼이 이미 존재할 때, repository의 create를 호출하지 않는지 테스트"""
    # given
    mock_repo = AsyncMock()
    mock_platform = SimpleNamespace(id=123)
    mock_repo.find_by_code.return_value = mock_platform

    mock_transaction = AsyncMock()
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=mock_transaction)

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    service = PlatformService(db_session_factory=mock_session_factory, platform_repo=mock_repo)

    # when
    result = await service.add_platform(PlatformCode.CHZZK, "치지직", "치즈")

    # then
    mock_repo.find_by_code.assert_awaited_once()
    mock_repo.create.assert_not_awaited()
    assert result == 123
