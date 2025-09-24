from unittest.mock import MagicMock

from celery import Celery
from sqlalchemy import text
from sqlalchemy.orm import Session

from chatzzk.services.collector.container import Container


def test_db_connection(db_session: Session):
    """테스트 DB 세션이 성공적으로 주입되고 쿼리가 실행되는지 확인합니다."""
    assert db_session is not None
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_container_config_is_for_test(test_container: Container):
    """DI 컨테이너가 테스트용 설정(local.test.env)을 사용하고 있는지 확인합니다."""
    # .env 파일에 설정된 테스트 DB 포트(5433)와 MinIO 포트(9001)를 사용하는지 검증
    db_url = str(test_container.config.db_config()["database_url"])
    minio_endpoint = test_container.config.storage_config()["endpoint"]

    assert "localhost:5433" in db_url
    assert "localhost:9001" in minio_endpoint


def test_celery_is_in_eager_mode(celery_app: Celery):
    """Celery가 태스크를 즉시 실행하는 Eager 모드인지 확인합니다."""
    assert celery_app.conf.task_always_eager is True


def test_chzzk_client_is_mocked(test_container: Container):
    """외부 API 클라이언트인 ChzzkPlatformClient가 Mock 객체로 대체되었는지 확인합니다."""
    chzzk_client_instance = test_container.chzzk_client()
    breakpoint()
    assert isinstance(chzzk_client_instance, MagicMock)
