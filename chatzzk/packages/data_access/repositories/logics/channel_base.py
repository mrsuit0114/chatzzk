from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.schemas.dto.repo_params.core.channel import ChannelCreateParams, ChannelFindParams
from chatzzk.packages.schemas.orm.models import ChannelORM


class ChannelLogicBase(Protocol):
    async def create_channel(self, session: AsyncSession, params: ChannelCreateParams) -> ChannelORM: ...

    async def find_channel(self, session: AsyncSession, params: ChannelFindParams) -> ChannelORM: ...
