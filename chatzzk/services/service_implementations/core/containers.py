from dependency_injector import containers, providers

from chatzzk.services.service_implementations.core.platform_service import PlatformService


class CoreContainer(containers.DeclarativeContainer):
    data_access = providers.DependenciesContainer()

    platform_service = providers.Factory(
        PlatformService,
        platform_repo=data_access.platform_repo,
    )
