from dependency_injector import containers, providers
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chatzzk_core.schemas.config import DataAccessConfig
from chatzzk_data_access.repositories import ChannelRepository, VODRepository
from chatzzk_data_access.storages import LocalStorage


# 앱 실행 용도는 transaction pooler 용 url
# 마이그레이션 용도는 direct db url을 사용할 것
async def init_db_engine(url: str, pool_size: int, max_overflow: int):
    logger.debug(f"🟢 [DataAccessContainer] Initializing DB Engine (Pool: {pool_size}+{max_overflow})...")

    engine = create_async_engine(
        url,
        # [설정 1] 풀 사이즈 환경변수 적용
        pool_size=pool_size,
        max_overflow=max_overflow,
        # [설정 2] Supabase Transaction Pooler 호환성 필수 설정
        # asyncpg가 Prepared Statement를 생성하지 않도록 강제함
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        },
    )
    try:
        yield engine
    finally:
        logger.debug("🔴 [DataAccessContainer] Disposing DB Engine...")
        await engine.dispose()
        logger.debug("⚫ [DataAccessContainer] DB Engine Disposed.")


class DataAccessContainer(containers.DeclarativeContainer):
    config = providers.Dependency(instance_of=DataAccessConfig)

    _db_engine = providers.Resource(
        init_db_engine,
        url=config.provided.db.database_url,
        pool_size=config.provided.db.pool_size,
        max_overflow=config.provided.db.max_overflow,
    )

    db_session_factory = providers.Resource(
        async_sessionmaker, bind=_db_engine, expire_on_commit=False, class_=AsyncSession
    )

    channel_repo = providers.Singleton(ChannelRepository)
    vod_repo = providers.Singleton(VODRepository)
    tmp_storage = providers.Singleton(LocalStorage, base_dir=config.provided.tmp_storage_base_dir)
