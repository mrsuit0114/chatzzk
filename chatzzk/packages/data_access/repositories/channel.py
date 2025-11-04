# 여기서 ORM을 제공함으로서 서비스에서는 세션을 한번 열었을 때 원자성을 보장할 수 있음
# 에그리거트를 관리함 - llm_meta_data는 채널에 종속적이기 때문에 따로 레포지토리를 구현하지 않고 channel에서 관리함

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.logics.channel_base import ChannelLogicBase
from chatzzk.packages.schemas.dto.repo_params.core.channel import ChannelCreateParams, ChannelFindParams
from chatzzk.packages.schemas.orm.models import Channel


class ChannelRepository:
    def __init__(self, channel_logic_factory: dict[PlatformCode, ChannelLogicBase]):
        self.factory = channel_logic_factory

    def _get_logic(self, platform_code: PlatformCode):
        logic_module = self.factory.get(platform_code)
        if logic_module:
            return logic_module
        else:
            raise ValueError(f"No logic module found for platform_code: {platform_code}")

    def create_platform_channel(
        self, session: AsyncSession, platform_code: PlatformCode, params: ChannelCreateParams
    ) -> Channel:
        logic_module = self._get_logic(platform_code)
        return logic_module.create_platform_channel(session, params)

    async def find_platform_channel(
        self, session: AsyncSession, platform_code: PlatformCode, params: ChannelFindParams
    ) -> Channel:
        logic_module = self._get_logic(platform_code)
        return await logic_module.find_platform_channel(session, params)

    async def find_channel_by_id(self, session: AsyncSession, channel_id: int) -> Channel:
        stmt = select(Channel).where(Channel.id == channel_id)

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    def update_channel(
        self,
        session: AsyncSession,
        channel: Channel,
        *,
        is_active: bool | None = None,
        last_vod_crawled_at: datetime | None = None,
    ) -> Channel:
        if is_active is not None:
            channel.is_active = is_active
        if last_vod_crawled_at is not None:
            channel.last_vod_crawled_at = last_vod_crawled_at

        session.add(channel)

        return channel

    # async def update_platform_channel
