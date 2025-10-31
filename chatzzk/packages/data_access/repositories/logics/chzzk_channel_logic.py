from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from chatzzk.packages.data_access.repositories.logics.channel_base import ChannelLogicBase
from chatzzk.packages.schemas.dto.repo_params.chzzk.channel import ChzzkChannelCreateParams, ChzzkChannelFindParams
from chatzzk.packages.schemas.orm.models import (
    ChannelLlmMetadataORM,
    ChannelORM,
    ChzzkChannelORM,
)


class ChzzkChannelLogic(ChannelLogicBase):
    def __init__(self, field_map: dict):
        self.field_map = field_map

    async def create_channel(self, session: AsyncSession, params: ChzzkChannelCreateParams) -> ChannelORM:
        channel = ChannelORM(platform_id=params.platform_id)

        chzzk_channel = ChzzkChannelORM(
            channel=channel,
            platform_channel_id=params.platform_channel_id,
            channel_name=params.channel_name,
            verified_mark=params.verified_mark,
        )

        channel_llm_metadata = ChannelLlmMetadataORM(channel=channel)

        session.add_all([channel, chzzk_channel, channel_llm_metadata])

        return channel

    async def find_channel(self, session: AsyncSession, params: ChzzkChannelFindParams) -> ChannelORM | None:
        filters = []

        # DTO에서 None이 아닌 값만 가져오기
        for key, value in params.model_dump(exclude_none=True).items():
            column = self.field_map.get(key)
            if column is not None:
                filters.append(column == value)

        stmt = (
            select(ChannelORM)
            .options(joinedload(ChannelORM.chzzk_channel))
            .join(ChzzkChannelORM, ChannelORM.id == ChzzkChannelORM.channel_id)
            .where(and_(*filters))
        )

        result = await session.execute(stmt)
        return result.scalars().first()
