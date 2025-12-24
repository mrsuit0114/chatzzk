from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk_core.constants import PlatformCode
from chatzzk_data_access.orm import Channel, Platform
from chatzzk_data_access.orm.models import ChannelMetadata


class ChannelRepository:
    async def get_active_channels_by_platform_code(
        self, session: AsyncSession, platform_code: PlatformCode
    ) -> Sequence[Channel]:
        """
        특정 플랫폼의 '활성(is_active=True)' 채널 목록을 조회합니다.
        Platform 테이블과 Join하여 한 번에 필터링합니다.
        """
        stmt = (
            select(Channel)
            .join(Channel.platform)  # INNER JOIN 생성
            .where(
                and_(
                    Channel.is_active.is_(True),  # 활성 상태 필터링
                    Platform.platform_code == platform_code,  # 플랫폼 코드 필터링
                )
            )
            # 만약 이후 로직에서 channel.platform 속성에 접근해야 한다면
            # joinedload를 사용하여 Eager Loading을 해야 N+1 문제를 막을 수 있습니다.
            # 단순히 ID와 CrawledAt만 필요하다면 없어도 됩니다.
            # .options(joinedload(Channel.platform))
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    async def update_last_crawled_at(self, session: AsyncSession, channel_id: int, scanned_at: datetime) -> None:
        stmt = update(Channel).where(Channel.id == channel_id).values(last_vod_crawled_at=scanned_at)
        await session.execute(stmt)

    async def get_channel_metadata_by_channel_id(self, session: AsyncSession, channel_id: int) -> dict:
        stmt = select(ChannelMetadata.metadata).where(ChannelMetadata.channel_id == channel_id)
        result = await session.execute(stmt)
        metadata = result.scalar_one_or_none()

        return metadata if metadata is not None else {}
