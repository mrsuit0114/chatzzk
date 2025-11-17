from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.schemas.api_models.chzzk import ChzzkChannelInfo
from chatzzk.packages.schemas.dto.api.chzzk.channel import ChzzkChannelAddRequestDTO, ChzzkChannelAddResponseDTO
from chatzzk.packages.schemas.dto.repo_params.chzzk.channel import ChzzkChannelCreateParams, ChzzkChannelFindParams
from chatzzk.services.interfaces.channel_management import ChannelManagementInterface


class ChzzkChannelManagementService(ChannelManagementInterface):
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        platform_repo: PlatformRepository,
        channel_repo: ChannelRepository,
        chzzk_api_client: ChzzkAPIClient,
    ):
        self.db_session_factory = db_session_factory
        self.platform_repo = platform_repo
        self.channel_repo = channel_repo
        self.api_client = chzzk_api_client
        self.platform_code = PlatformCode.CHZZK

    async def add_channel(self, dto: ChzzkChannelAddRequestDTO) -> ChzzkChannelAddResponseDTO:
        logger.info(f"Attempting to add new Chzzk channel: {dto.platform_channel_id}")

        channel_info: ChzzkChannelInfo | None = await self.api_client.fetch_channel_info(dto.platform_channel_id)
        if not channel_info:
            raise ValueError(f"Channel info for '{dto.platform_channel_id}' not found in Chzzk.")

        async with self.db_session_factory() as session:
            try:
                async with session.begin():
                    chzzk_platform = await self.platform_repo.find_by_platform_code(session, self.platform_code)
                    if not chzzk_platform:
                        raise RuntimeError("Chzzk platform must be registered in the database first.")

                    params = ChzzkChannelCreateParams(
                        platform_id=chzzk_platform.id,
                        platform_channel_id=channel_info.channel_id,
                        channel_name=channel_info.channel_name,
                        verified_mark=channel_info.verified_mark,
                    )
                    new_channel = self.channel_repo.create_platform_channel(session, self.platform_code, params)
                    await session.flush()

                    logger.success(f"Successfully added new Chzzk channel '{new_channel.chzzk_channel.channel_name}'.")

                    return ChzzkChannelAddResponseDTO(
                        platform_channel_id=new_channel.chzzk_channel.platform_channel_id,
                        channel_name=new_channel.chzzk_channel.channel_name,
                        verified_mark=new_channel.chzzk_channel.verified_mark,
                    )

            except IntegrityError as e:
                logger.warning(f"Chzzk channel '{dto.platform_channel_id}' already exists. Retrieving existing entry.")

                params = ChzzkChannelFindParams(platform_channel_id=dto.platform_channel_id)
                existing_channel = await self.channel_repo.find_channel_with_platform_channel(
                    session, self.platform_code, params
                )

                if existing_channel:
                    chzzk_channel = existing_channel.chzzk_channel
                    return ChzzkChannelAddResponseDTO(
                        platform_channel_id=chzzk_channel.platform_channel_id,
                        channel_name=chzzk_channel.channel_name,
                        verified_mark=chzzk_channel.verified_mark,
                    )
                else:
                    raise RuntimeError(
                        "Failed to add channel due to an unexpected race condition after an integrity error."
                    ) from e
