from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from chatzzk.packages.data_access.repositories.logics.channel_base import ChannelLogicBase
from chatzzk.packages.schemas.dto.repo_params.chzzk.channel import ChzzkChannelCreateParams, ChzzkChannelFindParams
from chatzzk.packages.schemas.orm.models import (
    Channel,
    ChannelLLMMetadata,
    ChannelMetadata,
    ChzzkChannel,
)


class ChzzkChannelLogic(ChannelLogicBase):
    def __init__(self, field_map: dict):
        self.field_map = field_map

    def create_platform_channel(self, session: AsyncSession, params: ChzzkChannelCreateParams) -> Channel:
        channel = Channel(
            platform_id=params.platform_id,
            chzzk_channel=ChzzkChannel(
                platform_channel_id=params.platform_channel_id,
                channel_name=params.channel_name,
                verified_mark=params.verified_mark,
            ),
            channel_llm_metadata=ChannelLLMMetadata(),
            channel_metadata=ChannelMetadata(),
        )

        session.add(channel)

        return channel

    async def find_platform_channel(self, session: AsyncSession, params: ChzzkChannelFindParams) -> Channel | None:
        filters = []

        # DTO에서 None이 아닌 값만 가져오기
        for key, value in params.model_dump(exclude_none=True).items():
            column = self.field_map.get(key)
            if column is not None:
                filters.append(column == value)

        stmt = (
            select(Channel)
            .options(joinedload(Channel.chzzk_channel))
            .join(ChzzkChannel, Channel.id == ChzzkChannel.channel_id)
            .where(and_(*filters))
        )

        result = await session.execute(stmt)
        return result.scalars().first()
