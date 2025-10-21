import os
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories import chzzk_channel_logic
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.schemas.clients.chzzk import ChannelInfo
from chatzzk.packages.schemas.orm.models import ChzzkChannelORM
from chatzzk.services.service_implementations.core.platform_service import PlatformService
from chatzzk.services.service_implementations.management.chzzk_channel_management_service import (
    ChzzkChannelManagementService,
)

pytestmark = pytest.mark.asyncio

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://testuser:testpass@localhost/testdb")


@pytest_asyncio.fixture(scope="module")
async def setup_database():
    """
    모듈 스코프로, 테스트 파일 실행 전 단 한 번 DB 스키마를 초기화합니다.
    Alembic을 사용하여 DB를 깨끗한 최신 상태로 만듭니다.
    """
    alembic_cfg = Config("alembic.ini")

    # DB를 초기 상태로 되돌리고 최신 버전으로 업그레이드
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield


@pytest_asyncio.fixture
async def db_session(setup_database):
    """
    각 테스트 함수마다 독립적인 트랜잭션을 보장하는 세션을 제공합니다.
    테스트 종료 후 롤백하여 다음 테스트에 영향을 주지 않습니다.
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    connection = await engine.connect()
    transaction = await connection.begin()

    SessionFactory = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    session = SessionFactory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest.fixture
def logic_registry():
    return {"chzzk": chzzk_channel_logic}


async def test_add_channel_integration(db_session: AsyncSession, logic_registry):
    """
    add_channel의 전체 흐름을 실제 DB와 연동하여 테스트합니다.
    1. 새로운 채널이 DB에 올바르게 저장되는지 검증합니다.
    2. 이미 존재하는 채널을 다시 추가하려 할 때, 중복 저장되지 않고 기존 ID를 반환하는지 검증합니다.
    """
    # given: 필요한 서비스와 레포지토리의 실제 인스턴스 생성
    # 단, 외부 API 클라이언트는 Mock으로 대체하여 실제 네트워크 통신을 방지
    mock_api_client = AsyncMock()

    # db_session을 직접 사용하는 대신, 테스트용 세션 팩토리를 만듭니다.
    test_session_factory = async_sessionmaker(bind=db_session.bind, expire_on_commit=False)

    platform_repo = PlatformRepository()
    channel_repo = ChannelRepository(logic_registry=logic_registry)

    platform_service = PlatformService(test_session_factory, platform_repo)
    channel_service = ChzzkChannelManagementService(test_session_factory, platform_repo, channel_repo, mock_api_client)

    # 1. 사전 조건: 'chzzk' 플랫폼을 DB에 추가
    await platform_service.add_platform(platform_code=PlatformCode.CHZZK, platform_name="치지직", donation_unit="치즈")

    # 2. Mock API 클라이언트 설정
    fake_channel_info = ChannelInfo(channel_id="test_chzzk_id_123", channel_name="테스트 스트리머", verified_mark=False)
    mock_api_client.fetch_channel_info.return_value = fake_channel_info

    # when: 1 - 새로운 채널 추가
    new_channel_id = await channel_service.add_channel(
        platform_code=PlatformCode.CHZZK.value, platform_channel_id="test_chzzk_id_123"
    )

    # then: 1 - DB에서 직접 확인하여 검증
    # 별도 세션으로 조회하여 commit 여부와 관계없이 확인 가능 (현재는 롤백되므로 같은 세션 사용)
    stmt = select(ChzzkChannelORM).where(ChzzkChannelORM.platform_channel_id == "test_chzzk_id_123")
    result = await db_session.execute(stmt)
    created_chzzk_channel = result.scalars().one_or_none()

    assert created_chzzk_channel is not None
    assert created_chzzk_channel.channel_name == "테스트 스트리머"
    assert created_chzzk_channel.channel_id == new_channel_id

    # when: 2 - 동일한 채널을 다시 추가 시도
    existing_channel_id = await channel_service.add_channel(
        platform_code=PlatformCode.CHZZK.value, platform_channel_id="test_chzzk_id_123"
    )

    # then: 2 - 반환된 ID가 기존 ID와 동일한지, API가 다시 호출되지 않았는지 확인
    assert existing_channel_id == new_channel_id
    # fetch_channel_info는 총 1번만 호출되어야 함 (처음 추가 시에만)
    mock_api_client.fetch_channel_info.assert_awaited_once()
