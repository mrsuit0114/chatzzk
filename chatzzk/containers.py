from dependency_injector import containers, providers

from chatzzk.packages.clients.containers import ClientsContainer
from chatzzk.packages.data_access.containers import DataAccessContainer
from chatzzk.services.service_implementations.management.containers import ManagementContainer


class AppContainer(containers.DeclarativeContainer):
    """
    애플리케이션의 모든 컨테이너를 조립하고 설정을 제공하는 최상위 컨테이너
    """

    config = providers.Configuration()

    data_access_package = providers.Container(DataAccessContainer, config=config.db)

    clients_package = providers.Container(
        ClientsContainer,
        config=config.api,
    )

    #
    management_service_package = providers.Container(
        ManagementContainer,
        db_session_factory=data_access_package.db_session_factory,
        platform_repo=data_access_package.platform_repo,
        channel_repo=data_access_package.channel_repo,
        chzzk_api_client=clients_package.chzzk_api_client,
    )
