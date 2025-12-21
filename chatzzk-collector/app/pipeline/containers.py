from dependency_injector import containers, providers

from app.pipeline.di_containers.client_containers import ClientContainer
from app.pipeline.di_containers.data_access_containers import DataAccessContainer
from app.pipeline.di_containers.service_containers import ServiceContainer
from chatzzk_core.schemas.config import Settings


class AppContainer(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)

    client_package = providers.Container(
        ClientContainer,
        config=settings.provided.clients,
    )

    data_access_package = providers.Container(
        DataAccessContainer,
        config=settings.provided.data_access,
    )

    service_package = providers.Container(
        ServiceContainer,
        config=settings.provided.services,
        client=client_package,
        data_access=data_access_package,
    )
