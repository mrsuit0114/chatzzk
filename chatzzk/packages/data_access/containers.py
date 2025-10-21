from dependency_injector import containers, providers

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.db.session import create_session_factory
from chatzzk.packages.data_access.repositories import chzzk_channel_logic
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository


class DataAccessContainer(containers.DeclarativeContainer):
    """data_access 패키지의 의존성을 관리하는 컨테이너"""

    config = providers.Configuration()

    db_session_factory = providers.Singleton(
        create_session_factory,
        database_url=config.db.database_url,
    )

    _logic_registry = {
        PlatformCode.CHZZK: chzzk_channel_logic,
    }

    _logic_registry_provider = providers.Object(_logic_registry)

    platform_repo = providers.Factory(PlatformRepository)

    channel_repo = providers.Factory(
        ChannelRepository,
        logic_registry=_logic_registry_provider,
    )

    vod_repo = providers.Factory(VodRepository, db_session_factory=db_session_factory)
