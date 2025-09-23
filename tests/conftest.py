from unittest.mock import MagicMock

import pytest
from alembic import command
from alembic.config import Config
from celery import Celery
from dependency_injector import providers

from chatzzk.packages.data_access.db.factory import create_db_engine
from chatzzk.packages.schemas.db_models import ChzzkChannelORM, PlatformORM
from chatzzk.services.collector.container import Container
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)
from chatzzk.services.collector.settings import CollectorSettings


@pytest.fixture(scope="session")
def celery_config():
    """테스트용 Celery 설정을 반환합니다. 브로커와 백엔드를 테스트용으로 지정합니다."""
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
    test_settings = CollectorSettings(_env_file="local.test.env")
    container = Container()
    container.config.from_pydantic(test_settings)

    container.db_engine.override(
        providers.Singleton(create_db_engine, db_config=providers.Object(test_settings.db_config))
    )

    container.wire(modules=celery_app.conf.include)

    with container.chzzk_client.override(MagicMock(spec=ChzzkPlatformClient)):
        yield container

    container.unwire()


@pytest.fixture(scope="function")
def db_session(test_container):
    """
    Alembic을 사용하여 테스트 DB 스키마를 최신으로 마이그레이션하고,
    테스트 종료 후 초기 상태로 되돌립니다.
    """
    # Alembic 설정 파일을 로드합니다.
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "base")
    # --- Setup ---
    # 현재 테스트를 위해 스키마를 최신 상태로 빌드합니다.
    command.upgrade(alembic_cfg, "head")

    session_provider = test_container.db_session_provider()
    with session_provider() as session:
        yield session


@pytest.fixture(scope="function")
def chzzk_channel_factory(db_session):
    """
    테스트용 '치지직' 플랫폼과 채널을 생성하는 팩토리 함수를 제공합니다.
    """
    # 1. 이 픽스처가 사용될 때 '치지직' 플랫폼을 미리 생성합니다.
    platform = PlatformORM(platform_code="chzzk", platform_name="치지직", donation_unit="치즈")
    db_session.add(platform)
    db_session.commit()

    def _create_channel(**kwargs):
        """
        채널을 생성하는 내부 함수. 기본값을 설정하고 kwargs로 오버라이드 가능.
        """
        channel_data = {
            "platform_id": platform.id,
            "channel_id": "test_channel_123",  # 기본값
            "channel_name": "테스트채널",  # 기본값
        }
        channel_data.update(kwargs)  # 테스트에서 넘겨준 값으로 덮어쓰기

        channel = ChzzkChannelORM(**channel_data)
        db_session.add(channel)
        db_session.commit()
        db_session.refresh(channel)
        return channel

    # 2. 채널을 생성하는 함수 자체를 반환합니다.
    return _create_channel
