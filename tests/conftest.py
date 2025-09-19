from unittest.mock import MagicMock

import pytest
from celery import Celery
from dependency_injector import providers

from chatzzk.packages.data_access.db.factory import create_db_engine
from chatzzk.packages.schemas.db_models import Base
from chatzzk.services.collector.container import Container
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient
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
    """컨테이너로부터 DB 엔진과 세션을 받아와 테이블을 관리합니다."""
    engine = test_container.db_engine()
    Base.metadata.create_all(bind=engine)

    session_provider = test_container.db_session_provider()
    with session_provider() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
