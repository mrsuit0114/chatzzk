from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.orm.models import PlatformORM
from chatzzk.packages.schemas.repositories.platform import PlatformCreateDTO


class PlatformRepository:
    async def find_by_code(self, session: AsyncSession, platform_code: PlatformCode) -> PlatformORM | None:
        stmt = select(PlatformORM).where(PlatformORM.platform_code == platform_code)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create(self, session: AsyncSession, dto: PlatformCreateDTO) -> PlatformORM:
        new_platform = PlatformORM(**dto.model_dump())
        session.add(new_platform)
        # flush를 통해 DB에 INSERT 쿼리를 보내고, 기본 키 등의 값을 받아옵니다.
        await session.flush()
        return new_platform
