import asyncio

from dependency_injector.wiring import Provide, inject
from loguru import logger

# 프로젝트 루트 경로를 sys.path에 추가
# project_root = Path(__file__).resolve().parent.parent
# sys.path.insert(0, str(project_root))
from chatzzk.containers import AppContainer
from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.schemas.config.settings import Settings
from chatzzk.packages.schemas.orm.models import PlatformORM


@inject
async def seed(
    channel_repo: ChannelRepository = Provide[AppContainer.data_access.channel_repo],
    session_factory=Provide[AppContainer.data_access.db_session_factory],
):
    """초기 데이터를 DB에 삽입합니다."""
    logger.info("Seeding initial data...")

    with session_factory() as session:
        # 1. 플랫폼 데이터 생성
        chzzk_platform = session.query(PlatformORM).filter_by(platform_code=PlatformCode.CHZZK).first()
        if not chzzk_platform:
            logger.info("Creating 'chzzk' platform...")
            chzzk_platform = PlatformORM(platform_code=PlatformCode.CHZZK, platform_name="치지직", donation_unit="치즈")
            session.add(chzzk_platform)
            session.commit()
            session.refresh(chzzk_platform)
        else:
            logger.info("'chzzk' platform already exists.")

        # 2. 수집할 채널 정보 정의
        channels_to_seed = [
            {"chzzk_channel_id": "c847a58a1599988f6154446c75366523", "channel_name": "도파"},
            {"chzzk_channel_id": "a6c4ddb09cdb160478996007bff35296", "channel_name": "아라하시 타비"},
        ]

        # 3. 채널 데이터 생성
        for ch_data in channels_to_seed:
            existing_channel = channel_repo.get_by_platform_id(PlatformCode.CHZZK, ch_data["chzzk_channel_id"])
            if existing_channel:
                logger.warning(f"Channel '{ch_data['channel_name']}' already exists. Skipping.")
                continue

            logger.info(f"Creating channel '{ch_data['channel_name']}'...")
            new_channel = channel_repo.create(platform=chzzk_platform, **ch_data)

            # 데이터 수집 허용 설정
            channel_repo.update_setting(new_channel.id, allow_data_collection=True)

    logger.success("✅ Data seeding complete.")


if __name__ == "__main__":
    container = AppContainer()
    container.config.from_pydantic(Settings())
    container.wire(modules=[__name__])
    asyncio.run(seed())
