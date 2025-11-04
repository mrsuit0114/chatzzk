from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.schemas.dto.repo_params.core.channel import ChannelCreateParams, ChannelFindParams
from chatzzk.packages.schemas.orm.models import Channel


class ChannelLogicBase(Protocol):
    def create_platform_channel(self, session: AsyncSession, params: ChannelCreateParams) -> Channel: ...

    async def find_platform_channel(self, session: AsyncSession, params: ChannelFindParams) -> Channel: ...
