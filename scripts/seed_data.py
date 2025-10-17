import asyncio

from dependency_injector.wiring import Provide, inject
from loguru import logger

from chatzzk.containers import AppContainer
from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.config.settings import Settings
from chatzzk.services.service_implementations.core.platform_service import PlatformService


@inject
async def seed(
    platform_service: PlatformService = Provide[AppContainer.core_services.platform_service],
):
    """DI 컨테이너를 통해 주입된 서비스를 사용하여 초기 데이터를 DB에 삽입합니다."""
    logger.info("Seeding initial data using services...")

    # 1. 플랫폼 데이터 추가
    platform_service.add_platform(platform_code=PlatformCode.CHZZK, platform_name="치지직", donation_unit="치즈")
    # 필요 시 다른 플랫폼도 추가
    # platform_service.add_platform(PlatformCode.YOUTUBE, ...)

    # # 2. 치지직 채널 데이터 추가
    # channels_to_add = [
    #     "c847a58a1599988f6154446c75366523", # 도파
    #     "a6c4ddb09cdb160478996007bff35296", # 아라하시 타비
    # ]

    # for channel_id in channels_to_add:
    #     try:
    #         new_id = chzzk_management_service.add_new_channel(channel_id)
    #         logger.info(f"Channel {channel_id} processed. System ID: {new_id}")
    #     except Exception as e:
    #         logger.error(f"Failed to add channel {channel_id}: {e}")

    # logger.success("✅ Data seeding complete.")


if __name__ == "__main__":
    container = AppContainer()
    container.config.from_pydantic(Settings())
    container.wire(modules=[__name__])
    asyncio.run(seed())
