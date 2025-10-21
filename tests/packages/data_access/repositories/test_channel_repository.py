from unittest.mock import AsyncMock, MagicMock

import pytest

from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.schemas.orm.models import ChannelORM, PlatformORM

pytestmark = pytest.mark.asyncio


async def test_create_calls_logic_module_and_session_methods():
    """
    ChannelRepository.create 호출 시, 로직 모듈을 올바르게 호출하고
    반환된 객체들로 session의 add_all, flush, refresh를 순서대로
    수행하는지 테스트합니다.
    """
    # given
    # 가짜 ORM 객체들 생성
    mock_orm_tuple = (MagicMock(spec=ChannelORM), MagicMock(), MagicMock())

    # 가짜 로직 모듈 설정
    mock_logic_module = MagicMock()
    mock_logic_module.create_channel.return_value = mock_orm_tuple

    # 가짜 로직 레지스트리 설정
    mock_logic_registry = {"chzzk": mock_logic_module}

    # 가짜 세션 설정
    mock_session = AsyncMock()
    mock_session.add_all = MagicMock()

    # 가짜 플랫폼 객체
    mock_platform = MagicMock(spec=PlatformORM)
    mock_platform.platform_code = "chzzk"

    # 가짜 DTO
    mock_dto = MagicMock()

    repo = ChannelRepository(logic_registry=mock_logic_registry)

    # when
    await repo.create(mock_session, mock_platform, mock_dto)

    # then
    # 1. 로직 모듈의 create_channel이 올바른 인자로 호출되었는가?
    mock_logic_module.create_channel.assert_called_once()

    # 2. session.add_all이 로직 모듈이 반환한 튜플로 호출되었는가?
    mock_session.add_all.assert_called_once_with(mock_orm_tuple)

    # 3. flush와 refresh가 await와 함께 호출되었는가?
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(mock_orm_tuple[0])
