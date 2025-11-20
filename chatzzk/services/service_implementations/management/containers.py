from dependency_injector import containers, providers

from chatzzk_constants.service_codes import PlatformCode
from chatzzk.services.service_implementations.management.chzzk_channel_management import ChzzkChannelManagementService
from chatzzk.services.service_implementations.management.platform_management import PlatformManagementService


class ManagementContainer(containers.DeclarativeContainer):
    db_session_factory = providers.Dependency()
    platform_repo = providers.Dependency()
    channel_repo = providers.Dependency()
    chzzk_api_client = providers.Dependency()

    platform_management = providers.Factory(
        PlatformManagementService, db_session_factory=db_session_factory, platform_repo=platform_repo
    )

    _chzzk_channel_management_service = providers.Factory(
        ChzzkChannelManagementService,
        db_session_factory=db_session_factory,
        platform_repo=platform_repo,
        channel_repo=channel_repo,
        chzzk_api_client=chzzk_api_client,
    )

    channel_factory = providers.Aggregate(
        {
            PlatformCode.CHZZK: _chzzk_channel_management_service,
        }
    )
