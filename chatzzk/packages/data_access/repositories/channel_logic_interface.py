from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.schemas.orm.models import ChannelORM, PlatformORM
from chatzzk.packages.schemas.repositories.channel import ChzzkChannelCreateDTO


class ChannelLogicInterface(Protocol):
    """
    각 플랫폼별 채널 로직 모듈이 반드시 구현해야 하는 함수들의 인터페이스를 정의합니다.
    """

    async def get_by_platform_id(self, session: AsyncSession, platform_channel_id: str) -> ChannelORM | None:
        """플랫폼 고유 ID로 채널 정보를 조회합니다."""
        ...

    def create_channel(self, platform: PlatformORM, dto: ChzzkChannelCreateDTO) -> ChannelORM:
        """새로운 채널과 관련 객체들을 생성합니다."""
        ...
