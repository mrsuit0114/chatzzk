from unittest.mock import MagicMock

import pytest
from celery.exceptions import Retry

from chatzzk.packages.schemas.db_models import ChzzkChannelORM


def test_discovery_task_success(celery_app, test_container, db_session):
    """
    discover_new_vods_for_channel Task 성공 시나리오를 테스트합니다.
    - @inject가 test_container에 연결되어 Mock 객체를 잘 주입하는지 검증합니다.
    """
    # --- 1. Arrange (준비) ---
    test_channel_id = "test_channel_123"
    channel = ChzzkChannelORM(channel_id=test_channel_id, channel_name="테스트채널")
    db_session.add(channel)
    db_session.commit()

    # Mock 객체 및 반환값 설정
    mock_service_instance = MagicMock()
    mock_service_instance.discover_and_save_new_vods.return_value = (5, 2)

    # --- 2. Act (실행) & 3. Assert (검증) ---
    with test_container.vod_discovery_service.override(mock_service_instance):
        task = celery_app.tasks["collector.discover_new_vods"]
        result = task.delay(channel_id=test_channel_id)
        assert result.successful()
        assert "Completed for test_channel_123" in result.get()
        mock_service_instance.discover_and_save_new_vods.assert_called_once_with(channel_id=test_channel_id)


def test_discovery_task_failure_and_retry(celery_app, test_container, db_session):
    """
    서비스에서 예외 발생 시, Task가 재시도를 요청하는지 테스트합니다.
    """
    # --- 1. Arrange (준비) ---
    test_channel_id = "test_channel_456"
    mock_service_instance = MagicMock()
    mock_service_instance.discover_and_save_new_vods.side_effect = ConnectionError("API Failed")
    task = celery_app.tasks["collector.discover_new_vods"]

    # --- 2. Act (실행) & 3. Assert (검증) ---
    from unittest.mock import patch

    with (
        test_container.vod_discovery_service.override(mock_service_instance),
        patch.object(task, "retry", side_effect=Retry) as mock_retry,
    ):
        with pytest.raises(Retry):
            task.delay(channel_id=test_channel_id)

        mock_service_instance.discover_and_save_new_vods.assert_called_once_with(channel_id=test_channel_id)
        mock_retry.assert_called_once()
        assert isinstance(mock_retry.call_args.kwargs["exc"], ConnectionError)
