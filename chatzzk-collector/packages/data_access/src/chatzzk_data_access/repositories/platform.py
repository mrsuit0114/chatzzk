from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk_core.constants import PlatformCode
from chatzzk_data_access.orm import Platform

# 메서드 네이밍 - get_{entity}_(with_{entity})_by_{condition}


class PlatformRepository:
    async def get_platform_by_code(self, session: AsyncSession, platform_code: PlatformCode) -> Platform:
        stmt = select(Platform).where(Platform.platform_code == platform_code)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_all_platform_codes(self, session: AsyncSession) -> list[PlatformCode]:
        stmt = select(Platform.platform_code)
        result = await session.execute(stmt)
        return [row for row in result.scalars().all()]
