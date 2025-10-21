from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkApiClient
from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.schemas.clients.chzzk import ChannelInfo
from chatzzk.packages.schemas.repositories.channel import ChzzkChannelCreateDTO
from chatzzk.services.interfaces.service_implementations.channel_management import ChannelManagement


class ChzzkChannelManagementService(ChannelManagement):
    """PlatformManagement 인터페이스의 치지직 플랫폼 구현체"""

    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        platform_repo: PlatformRepository,
        channel_repo: ChannelRepository,
        chzzk_api_client: ChzzkApiClient,
    ):
        self.db_session_factory = db_session_factory
        self.platform_repo = platform_repo
        self.channel_repo = channel_repo
        self.api_client = chzzk_api_client

    async def add_channel(self, platform_code: str, platform_channel_id: str) -> int:
        """
        채널을 DB에 추가합니다.
        이미 존재하는 경우 해당 채널의 id를를 반환합니다.
        """
        if platform_code != PlatformCode.CHZZK.value:
            raise ValueError(f"This service only supports '{PlatformCode.CHZZK.value}'.")

        logger.info(f"Attempting to add new Chzzk channel: {platform_channel_id}")

        async with self.db_session_factory() as session:
            async with session.begin():
                chzzk_platform = await self.platform_repo.find_by_code(session, platform_code)
                if chzzk_platform is None:
                    raise ValueError(f"platform not found in db: {platform_code}")

                existing_channel = await self.channel_repo.find_by_platform_channel_id(
                    session, chzzk_platform, platform_channel_id
                )
                if existing_channel:
                    logger.warning(f"Channel {platform_channel_id} already exists. Returning existing channel id.")
                    return existing_channel.id

                channel_info: ChannelInfo | None = await self.api_client.fetch_channel_info(platform_channel_id)
                if not channel_info:
                    raise ValueError(f"not found channel_info of {platform_channel_id} in chzzk")

                logger.info(f"Creating new channel '{channel_info.channel_name}' in DB.")

                dto = ChzzkChannelCreateDTO(
                    platform_channel_id=channel_info.channel_id,
                    channel_name=channel_info.channel_name,
                    is_verified=channel_info.verified_mark,
                )

                new_channel = await self.channel_repo.create(session=session, platform=chzzk_platform, dto=dto)

                return new_channel.id

    def sync_channel(self, channel_id: int) -> None:
        # TODO: 채널 정보 동기화 로직 구현
        pass
