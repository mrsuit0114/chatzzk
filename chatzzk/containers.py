from dependency_injector import containers, providers

from chatzzk.packages.clients.containers import ClientsContainer
from chatzzk.packages.data_access.containers import DataAccessContainer
from chatzzk.services.service_implementations.core.containers import CoreContainer


class AppContainer(containers.DeclarativeContainer):
    """
    애플리케이션의 모든 컨테이너를 조립하고 설정을 제공하는 최상위 컨테이너
    """

    config = providers.Configuration()

    # 1. 최하위 계층 컨테이너 (외부 패키지)
    data_access = providers.Container(
        DataAccessContainer,
        config=config,
    )

    clients = providers.Container(
        ClientsContainer,
        config=config,
    )

    # 2. 서비스 계층 컨테이너
    core_services = providers.Container(
        CoreContainer,
        data_access=data_access,
    )
