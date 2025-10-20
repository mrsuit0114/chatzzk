from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.schemas.repositories.platform import PlatformCreateDTO

pytestmark = pytest.mark.asyncio


async def test_find_by_code_existing():
    """find_by_code 호출 시, DB에 플랫폼이 존재하면 해당 객체를 반환하는지 테스트"""
    # given
    mock_platform = SimpleNamespace(id=123)
    mock_session = AsyncMock()

    # Result, scalars(), first() 체인을 정확히 모킹
    mock_scalar_result = MagicMock()
    mock_scalar_result.first.return_value = mock_platform

    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=mock_scalar_result)

    mock_session.execute.return_value = mock_result

    repo = PlatformRepository()

    # when
    result = await repo.find_by_code(mock_session, PlatformCode.CHZZK)

    # then
    assert result == mock_platform
    mock_session.execute.assert_awaited_once()


async def test_create():
    """create 호출 시, 올바른 데이터로 ORM 객체를 생성하고 DB에 추가하는지 테스트"""
    # patch를 사용하여 PlatformORM의 생성을 감시
    with patch("chatzzk.packages.data_access.repositories.platform.PlatformORM") as mock_platform_orm:
        # given
        mock_session = AsyncMock()
        repo = PlatformRepository()
        mock_session.add = MagicMock()  # 동기 메서드

        test_platform_name = "test_platform"
        test_pl_code = PlatformCode.CHZZK
        test_donation_u = "test_dollor"

        # when

        dto = PlatformCreateDTO(
            platform_code=test_pl_code, platform_name=test_platform_name, donation_unit=test_donation_u
        )
        await repo.create(mock_session, dto)

        # then
        mock_platform_orm.assert_called_once_with(**dto.model_dump())
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()
