from dependency_injector import containers, providers
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chatzzk_core.schemas.config.data_access.data_access import DataAccessConfig
from chatzzk_data_access.repositories.channel import ChannelRepository
from chatzzk_data_access.repositories.vod import VODRepository
from chatzzk_data_access.storages.local_storage import LocalStorage


async def init_db_engine(url: str):
    logger.debug("🟢 [DataAccessContainer] Initializing DB Engine...")
    engine = create_async_engine(url)
    try:
        yield engine
    finally:
        logger.debug("🔴 [DataAccessContainer] Disposing DB Engine...")
        await engine.dispose()
        logger.debug("⚫ [DataAccessContainer] DB Engine Disposed.")


class DataAccessContainer(containers.DeclarativeContainer):
    config: providers.Dependency(instance_of=DataAccessConfig) = providers.Dependency()

    _db_engine = providers.Resource(init_db_engine, url=config.provided.db.database_url)

    db_session_factory = providers.Resource(
        async_sessionmaker, bind=_db_engine, expire_on_commit=False, class_=AsyncSession
    )

    channel_repo = providers.Singleton(ChannelRepository)
    vod_repo = providers.Singleton(VODRepository)
    tmp_storage = providers.Singleton(LocalStorage, base_dir=config.provided.tmp_storage_base_dir)
