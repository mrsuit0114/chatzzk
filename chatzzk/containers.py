from dependency_injector import containers, providers

from chatzzk.packages.clients.containers import ClientsContainer
from chatzzk.packages.data_access.containers import DataAccessContainer


class AppContainer(containers.DeclarativeContainer):
    """
    애플리케이션의 모든 의존성을 관리하는 메인 컨테이너
    """

    config = providers.Configuration()

    data_access = providers.Container(
        DataAccessContainer,
        config=config,
    )

    clients = providers.Container(
        ClientsContainer,
        config=config,
    )
