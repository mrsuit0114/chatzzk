from dependency_injector import containers, providers

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.config.discovery import DiscoveryServiceConfig
from chatzzk.services.service_implementations.discovery.chzzk_vod_discovery import ChzzkVODDiscoveryService


class DiscoveryContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_session_factory = providers.Dependency()
    channel_repo = providers.Dependency()
    vod_repo = providers.Dependency()
    chzzk_api_client = providers.Dependency()

    discovery_config = providers.Callable(DiscoveryServiceConfig.model_validate, config)

    chzzk_discovery_service = providers.Factory(
        ChzzkVODDiscoveryService,
        db_session_factory=db_session_factory,
        channel_repo=channel_repo,
        vod_repo=vod_repo,
        chzzk_api_client=chzzk_api_client,
        config=discovery_config,
    )

    platform_discovery_factory = providers.FactoryAggregate({PlatformCode.CHZZK: chzzk_discovery_service})
