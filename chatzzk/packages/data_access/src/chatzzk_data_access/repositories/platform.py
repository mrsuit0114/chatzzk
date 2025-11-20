from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk_constants.service_codes import PlatformCode
from chatzzk_schemas.orm.models import Platform


class PlatformRepository:
    async def find_by_platform_code(self, session: AsyncSession, platform_code: PlatformCode) -> Platform | None:
        stmt = select(Platform).where(Platform.platform_code == platform_code)
        result = await session.execute(stmt)
        return result.scalars().first()

    def create(
        self, session: AsyncSession, platform_code: PlatformCode, platform_name: str, donation_unit: str
    ) -> Platform:
        new_platform = Platform(platform_code=platform_code, platform_name=platform_name, donation_unit=donation_unit)
        session.add(new_platform)
        return new_platform
