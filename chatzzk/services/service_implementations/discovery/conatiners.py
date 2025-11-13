from dependency_injector import containers, providers

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.config.services.vod_discovery import ChzzkVODDiscoveryServiceConfig
from chatzzk.services.service_implementations.discovery.chzzk_vod_discovery import ChzzkVODDiscoveryService


class DiscoveryContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_session_factory = providers.Dependency()
    channel_repo = providers.Dependency()
    vod_repo = providers.Dependency()
    chzzk_api_client = providers.Dependency()

    _chzzk_discovery_config = providers.Callable(ChzzkVODDiscoveryServiceConfig.model_validate, config.chzzk)

    chzzk_discovery_service = providers.Factory(
        ChzzkVODDiscoveryService,
        db_session_factory=db_session_factory,
        channel_repo=channel_repo,
        vod_repo=vod_repo,
        chzzk_api_client=chzzk_api_client,
        config=_chzzk_discovery_config,
    )

    vod_discovery_factory = providers.FactoryAggregate({PlatformCode.CHZZK: chzzk_discovery_service})
