from dependency_injector import containers, providers

from chatzzk.services.collector.chzzk.chzzk_service import ChzzkCollectorService


class CollectorContainer(containers.DeclarativeContainer):
    """collector 서비스의 의존성을 관리하는 컨테이너"""

    clients = providers.DependenciesContainer()
    data_access = providers.DependenciesContainer()

    chzzk_collector_service = providers.Factory(
        ChzzkCollectorService,
        chzzk_api_client=clients.chzzk_api_client,
        channel_repo=data_access.channel_repo,
        vod_repo=data_access.vod_repo,
    )
