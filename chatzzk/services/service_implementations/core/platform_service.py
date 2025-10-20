from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.schemas.repositories.platform import PlatformCreateDTO


class PlatformService:
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession], platform_repo: PlatformRepository):
        self.db_session_factory = db_session_factory
        self.platform_repo = platform_repo

    async def add_platform(self, platform_code: PlatformCode, platform_name: str, donation_unit: str) -> int:
        """
        새로운 플랫폼을 DB에 등록하거나, 이미 존재하면 기존 정보를 반환합니다.
        """
        logger.info(f"Attempting to add platform: {platform_name}")
        async with self.db_session_factory() as session:
            async with session.begin():  # 트랜잭션 시작 (commit/rollback 자동 관리)
                existing = await self.platform_repo.find_by_code(session, platform_code)
                if existing:
                    logger.info(f"Already existing platform: {platform_code.value}")
                    return existing.id

                dto = PlatformCreateDTO(
                    platform_code=platform_code, platform_name=platform_name, donation_unit=donation_unit
                )
                new_platform = await self.platform_repo.create(session, dto)
                return new_platform.id

    async def get_platform_by_code(self, platform_code: PlatformCode) -> int:
        """플랫폼 코드로 ID를 조회합니다."""
        async with self.db_session_factory() as session:
            platform = await self.platform_repo.find_by_code(session, platform_code)
            if not platform:
                raise ValueError(f"Platform '{platform_code.value}' not found in DB.")
            return platform.id
