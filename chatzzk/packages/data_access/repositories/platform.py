from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.orm.models import PlatformORM


class PlatformRepository:
    async def find_by_platform_code(self, session: AsyncSession, platform_code: PlatformCode) -> PlatformORM | None:
        stmt = select(PlatformORM).where(PlatformORM.platform_code == platform_code)
        result = await session.execute(stmt)
        return result.scalars().first()

    def create(
        self, session: AsyncSession, platform_code: PlatformCode, platform_name: str, donation_unit: str
    ) -> PlatformORM:
        new_platform = PlatformORM(
            platform_code=platform_code, platform_name=platform_name, donation_unit=donation_unit
        )
        session.add(new_platform)
        return new_platform
