from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_core.constants import PlatformCode
from chatzzk_data_access.repositories import PlatformRepository


class PlatformService:
    def __init__(
        self,
        platform_repo: PlatformRepository,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        self.platform_repo = platform_repo
        self.db_session_factory = db_session_factory

    async def list_all_platform_codes(self) -> list[PlatformCode]:
        async with self.db_session_factory() as session:
            return await self.platform_repo.get_all_platform_codes(session)
