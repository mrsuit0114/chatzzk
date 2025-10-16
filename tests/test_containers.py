import pytest

from chatzzk.containers import AppContainer
from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.schemas.config.settings import Settings


@pytest.fixture(scope="module")
def app_container() -> AppContainer:
    """테스트를 위한 AppContainer 인스턴스를 생성하는 pytest fixture"""
    container = AppContainer()
    container.config.from_pydantic(Settings())
    # 테스트 환경을 위한 별도의 설정 파일을 사용하도록 오버라이드 할 수도 있습니다.
    # container.config.from_yaml("config.test.yml")
    return container


def test_container_wiring(app_container: AppContainer):
    """
    컨테이너의 모든 의존성이 올바르게 연결되었는지 검증합니다.
    check_dependencies()는 하나라도 잘못된 설정이 있으면 예외를 발생시킵니다.
    """
    try:
        app_container.check_dependencies()
    except Exception as e:
        pytest.fail(f"Container wiring check failed: {e}")


def test_provider_types(app_container: AppContainer):
    """
    각 provider가 올바른 타입의 객체를 생성하는지 검증합니다.
    """
    # data_access 레이어 검증
    channel_repo = app_container.data_access.channel_repo()
    assert isinstance(channel_repo, ChannelRepository)

    # clients 레이어 검증
    base_http_client = app_container.clients.base_http_client()
    assert isinstance(base_http_client, BaseHttpClient)


def test_singleton_and_factory_behavior(app_container: AppContainer):
    """
    Singleton과 Factory provider가 의도대로 동작하는지 검증합니다.
    """
    # Singleton provider는 다른 인스턴스를 반환해야 합니다.
    http_client_1 = app_container.clients.base_http_client()
    http_client_2 = app_container.clients.base_http_client()
    assert http_client_1 is http_client_2

    # Factory provider는 항상 새로운 인스턴스를 반환해야 합니다.
    repo_1 = app_container.data_access.channel_repo()
    repo_2 = app_container.data_access.channel_repo()
    assert repo_1 is not repo_2
