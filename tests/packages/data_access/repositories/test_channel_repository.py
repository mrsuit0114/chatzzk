import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from chatzzk.packages.data_access.db.session import create_session_factory
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.schemas.orm.models import (
    ChannelORM,
    ChannelSettingORM,
    ChzzkChannelORM,
    PlatformORM,
)


@pytest.fixture(scope="function")
def db_session_factory() -> sessionmaker:
    """
    alembic.ini에 설정된 테스트 DB를 사용하고, 각 테스트마다 스키마를 초기화하는 fixture.
    """
    alembic_cfg = Config("alembic.ini")
    database_url = alembic_cfg.get_main_option("sqlalchemy.url")

    # 1. 이전 실행에서 남았을 수 있는 ENUM 타입을 먼저 삭제
    engine = create_engine(database_url)
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(text("DROP TYPE IF EXISTS vodprocessstatus CASCADE"))
            connection.execute(text("DROP TYPE IF EXISTS resultobjectfiletype CASCADE"))
    engine.dispose()

    # 2. DB를 초기 상태로 되돌리고 최신 스키마로 업그레이드
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    # 3. 테스트에 사용할 세션 팩토리를 생성하여 반환
    return create_session_factory(database_url)


@pytest.fixture(scope="function")
def db_session(db_session_factory: sessionmaker) -> Session:
    """
    각 테스트 함수에 대해 독립적인 트랜잭션을 보장하는 세션을 제공합니다.
    테스트 종료 후 모든 변경사항을 롤백하여 테스트 간 격리를 보장합니다.
    """
    session = db_session_factory()
    try:
        yield session
    finally:
        session.rollback()  # 모든 변경사항을 롤백
        session.close()


def test_get_by_platform_id_returns_channel_with_eager_loaded_data(
    db_session_factory: sessionmaker, db_session: Session
):
    """
    `get_by_platform_id` 성공 케이스 테스트.

    Given:
        - 특정 플랫폼('chzzk')과 채널 정보를 DB에 미리 저장.
    When:
        - 해당 채널의 `platform_code`와 `platform_channel_id`로 레포지토리 메서드를 호출.
    Then:
        - `ChannelORM` 객체가 정상적으로 반환되어야 함.
        - 반환된 객체에는 `platform`, `chzzk_channel`, `setting` 속성이 추가 쿼리 없이
          즉시 사용할 수 있도록 로드되어 있어야 함 (Eager Loading 검증).
    """
    # Given: 테스트 데이터 준비
    platform = PlatformORM(platform_code="chzzk", platform_name="치지직", donation_unit="원")
    db_session.add(platform)
    db_session.commit()

    generic_channel = ChannelORM(platform_id=platform.id)
    chzzk_channel = ChzzkChannelORM(
        channel_id="test_chzzk_id",
        channel_name="테스트 채널",
        is_verified=True,
    )
    setting = ChannelSettingORM(allow_data_collection=True)

    chzzk_channel.channel = generic_channel
    setting.channel = generic_channel

    db_session.add(generic_channel)
    db_session.commit()

    # When: 레포지토리 메서드 실행
    repo = ChannelRepository(db_session_factory)
    found_channel = repo.get_by_platform_id(platform_code="chzzk", platform_channel_id="test_chzzk_id")

    # Then: 결과 검증
    assert found_channel is not None
    assert isinstance(found_channel, ChannelORM)

    # Eager Loading 검증
    assert found_channel.platform is not None
    assert found_channel.chzzk_channel is not None
    assert found_channel.setting is not None

    assert found_channel.platform.platform_code == "chzzk"
    assert found_channel.chzzk_channel.channel_name == "테스트 채널"
    assert found_channel.setting.allow_data_collection is True


def test_get_by_platform_id_returns_none_for_nonexistent_id(db_session_factory: sessionmaker):
    """
    `get_by_platform_id` 실패 케이스 (데이터 없음) 테스트.

    Given:
        - 비어있는 DB.
    When:
        - 존재하지 않는 `platform_channel_id`로 레포지토리 메서드를 호출.
    Then:
        - `None`이 반환되어야 함.
    """
    # Given: 비어있는 DB

    # When: 레포지토리 메서드 실행
    repo = ChannelRepository(db_session_factory)
    found_channel = repo.get_by_platform_id(platform_code="chzzk", platform_channel_id="nonexistent_id")

    # Then: 결과 검증
    assert found_channel is None


def test_create_channel_successfully(db_session_factory: sessionmaker, db_session: Session):
    """
    `create` 메서드 성공 케이스 테스트.

    Given:
        - 채널을 등록할 플랫폼('chzzk') 정보가 DB에 미리 저장되어 있음.
        - 생성할 채널의 상세 정보 (kwargs).
    When:
        - `create` 메서드를 호출하여 채널 생성을 요청.
    Then:
        - 반환된 `ChannelORM` 객체가 유효해야 함.
        - 별도의 세션으로 DB를 다시 조회했을 때, `ChannelORM`, `ChzzkChannelORM`,
          `ChannelSettingORM` 등 모든 연관 객체들이 정확한 데이터로 생성되어 있어야 함
          (원자적 생성 및 cascade 동작 검증).
    """
    # Given: 플랫폼 데이터 미리 준비
    platform = PlatformORM(platform_code="chzzk", platform_name="치지직", donation_unit="원")
    db_session.add(platform)
    db_session.commit()

    repo = ChannelRepository(db_session_factory)
    create_kwargs = {
        "chzzk_channel_id": "test_create_id",
        "channel_name": "새로 생성된 채널",
        "is_verified": True,
    }

    # When: create 메서드 호출
    new_channel = repo.create(platform=platform, **create_kwargs)

    # Then: 결과 검증
    # 1. 반환된 객체 검증
    assert new_channel is not None
    assert isinstance(new_channel, ChannelORM)
    assert new_channel.id is not None
    assert new_channel.platform_id == platform.id

    # 2. DB에 실제 데이터가 올바르게 저장되었는지, 별도 세션으로 다시 조회하여 검증
    with db_session_factory() as session:
        # 제네릭 채널 조회
        channel_in_db = session.get(ChannelORM, new_channel.id)
        assert channel_in_db is not None

        # 상세 채널(chzzk) 조회 및 검증
        chzzk_channel_in_db = session.query(ChzzkChannelORM).filter(ChzzkChannelORM.id == new_channel.id).one_or_none()
        assert chzzk_channel_in_db is not None
        assert chzzk_channel_in_db.channel_name == "새로 생성된 채널"

        # 설정 객체 조회 및 검증
        setting_in_db = (
            session.query(ChannelSettingORM).filter(ChannelSettingORM.channel_id == new_channel.id).one_or_none()
        )
        assert setting_in_db is not None
        # ORM 모델에 정의된 default 값이 올바르게 설정되었는지 확인
        assert setting_in_db.allow_data_collection is False
