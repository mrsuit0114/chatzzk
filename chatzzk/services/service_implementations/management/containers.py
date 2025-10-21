from dependency_injector import containers, providers

from chatzzk.services.service_implementations.management.chzzk_channel_management_service import (
    ChzzkChannelManagementService,
)


class ManagementContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    data_access = providers.DependenciesContainer()
    clients = providers.DependenciesContainer()

    chzzk_channel_management_service = providers.Factory(
        ChzzkChannelManagementService,
        db_session_factory=data_access.db_session_factory,
        platform_repo=data_access.platform_repo,
        channel_repo=data_access.channel_repo,
        chzzk_api_client=clients.chzzk_api_client,
    )

    # youtube_channel_management_service  ..

    # chzzk_vod_management_service

    channel_service_factory = providers.FactoryAggregate(
        chzzk=chzzk_channel_management_service,
        # youtube = ...
    )
