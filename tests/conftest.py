from unittest.mock import MagicMock

import pytest
from alembic import command
from alembic.config import Config
from celery import Celery
from sqlalchemy.orm import sessionmaker

from chatzzk.packages.schemas.db_models import ChzzkChannelORM, PlatformORM
from chatzzk.services.collector.container import Container
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)
from chatzzk.services.collector.settings import collector_settings


@pytest.fixture(scope="session")
def celery_config():
    """테스트용 Celery 설정을 반환합니다. 브로커와 백엔드를 메모리 기반으로 지정합니다."""
    from chatzzk.services.collector.celery_app import TASK_MODULES

    return {
        "broker_url": "memory://",
        "result_backend": "rpc://",
        "task_always_eager": True,
        "task_eager_propagates": True,
        "include": TASK_MODULES,
    }


@pytest.fixture(scope="session")
def celery_app(celery_config):
    """위의 테스트 설정을 사용하여 Celery 앱 인스턴스를 생성합니다."""
    app = Celery("collector")
    app.conf.update(**celery_config)
    return app


@pytest.fixture(scope="session")
def test_container(celery_app):
    """테스트용 DI 컨테이너를 생성하고, Task 모듈과 연결(wire)합니다."""
    container = Container()
    # local.test.env 파일의 설정을 자동으로 로드합니다.
    container.config.from_pydantic(collector_settings)

    container.wire(modules=celery_app.conf.include)

    # ChzzkPlatformClient를 Mock 객체로 대체합니다.
    with container.chzzk_client.override(MagicMock(spec=ChzzkPlatformClient)):
        yield container

    container.unwire()


@pytest.fixture(scope="session")
def migrated_db_engine(test_container):
    """세션 스코프 Fixture: 테스트 세션 시작 시 DB를 마이그레이션합니다."""
    alembic_cfg = Config("alembic.ini")
    engine = test_container.db_engine()

    # DB를 초기 상태로 돌렸다가 최신으로 마이그레이션 (세션 당 한 번)
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield engine


@pytest.fixture(scope="function")
def db_session(migrated_db_engine):
    """
    함수 스코프 Fixture: 각 테스트마다 트랜잭션을 사용하여 DB를 격리합니다.
    테스트 종료 후 롤백하여 훨씬 빠른 속도를 제공합니다.
    """
    connection = migrated_db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def chzzk_channel_factory(db_session):
    """
    테스트용 '치지직' 플랫폼과 채널을 생성하는 팩토리 함수를 제공합니다.
    """
    platform = PlatformORM(platform_code="chzzk", platform_name="치지직", donation_unit="치즈")
    db_session.add(platform)
    db_session.commit()

    def _create_channel(**kwargs):
        channel_data = {
            "platform_id": platform.id,
            "channel_id": "test_channel_123",
            "channel_name": "테스트채널",
        }
        channel_data.update(kwargs)

        channel = ChzzkChannelORM(**channel_data)
        db_session.add(channel)
        db_session.commit()
        db_session.refresh(channel)
        return channel

    return _create_channel
