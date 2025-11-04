from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.logics.chzzk_channel_logic import ChzzkChannelLogic
from chatzzk.packages.data_access.repositories.logics.chzzk_vod_logic import ChzzkVODLogic
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.data_access.repositories.vod import VODRepository
from chatzzk.packages.schemas.orm.models import ChzzkChannel


class DataAccessContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    _db_engine = providers.Resource(create_async_engine, config.database_url)

    db_session_factory = providers.Resource(
        async_sessionmaker, bind=_db_engine, expire_on_commit=False, class_=AsyncSession
    )

    _chzzk_field_map = {
        "platform_channel_id": ChzzkChannel.platform_channel_id,
        "channel_name": ChzzkChannel.channel_name,
        "verified_mark": ChzzkChannel.verified_mark,
    }

    _channel_repo_logics = providers.Object({PlatformCode.CHZZK: ChzzkChannelLogic(_chzzk_field_map)})
    _vod_repo_logics = providers.Object({PlatformCode.CHZZK: ChzzkVODLogic()})

    platform_repo = providers.Singleton(PlatformRepository)
    channel_repo = providers.Singleton(
        ChannelRepository,
        channel_logic_factory=_channel_repo_logics,
    )
    vod_repo = providers.Singleton(
        VODRepository,
        vod_logic_factory=_vod_repo_logics,
    )
