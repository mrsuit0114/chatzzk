from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_data_access.repositories.platform import PlatformRepository
from chatzzk_schemas.dto.api.core.platform import PlatformAddRequestDTO, PlatformAddResponseDTO
from chatzzk.services.interfaces.platform_management import PlatformManagementInterface


class PlatformManagementService(PlatformManagementInterface):
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession], platform_repo: PlatformRepository):
        self.db_session_factory = db_session_factory
        self.platform_repo = platform_repo

    async def add_platform(self, dto: PlatformAddRequestDTO) -> PlatformAddResponseDTO:
        logger.info(f"Attempting to add platform: {dto.platform_name}")

        async with self.db_session_factory() as session:
            try:
                async with session.begin():
                    new_platform = self.platform_repo.create(
                        session,
                        platform_code=dto.platform_code,
                        platform_name=dto.platform_name,
                        donation_unit=dto.donation_unit,
                    )
                    await session.flush()

                    logger.success(f"Successfully added new platform '{dto.platform_name}'.")
                    return PlatformAddResponseDTO(platform_id=new_platform.id)

            except IntegrityError as e:
                logger.warning(f"Platform '{dto.platform_code.value}' already exists. Retrieving existing entry.")
                existing_platform = await self.platform_repo.find_by_platform_code(
                    session, platform_code=dto.platform_code
                )

                if existing_platform:
                    return PlatformAddResponseDTO(platform_id=existing_platform.id)
                else:
                    # 동시성 이슈로 방금 IntegrityError를 발생시킨 데이터가 삭제되는 등
                    # 매우 드문 예외 상황에 대한 방어 코드
                    raise RuntimeError(
                        "Failed to add platform due to an unexpected race condition after an integrity error."
                    ) from e
