from dependency_injector import containers, providers

from chatzzk.services.service_implementations.core.platform_service import PlatformService


class CoreContainer(containers.DeclarativeContainer):
    data_access = providers.DependenciesContainer()

    platform_service = providers.Factory(
        PlatformService,
        db_session_factory=data_access.db_session_factory,
        platform_repo=data_access.platform_repo,
    )
