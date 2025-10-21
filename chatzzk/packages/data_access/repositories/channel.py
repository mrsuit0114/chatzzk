from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.channel_logic_interface import ChannelLogicInterface
from chatzzk.packages.schemas.orm.models import (
    ChannelORM,
    PlatformORM,
)
from chatzzk.packages.schemas.repositories.channel import ChzzkChannelCreateDTO


class ChannelRepository:
    """플랫폼 중립적인 채널 애그리거트 데이터 접근을 캡슐화합니다."""

    def __init__(self, logic_registry: dict[str, ChannelLogicInterface]):
        self.logic_registry: dict[PlatformCode, ChannelLogicInterface] = logic_registry

    def _get_logic_module(self, platform_code: str):
        logic_module = self.logic_registry.get(platform_code)
        if not logic_module:
            raise ValueError(f"Unsupported platform code: {platform_code}")
        return logic_module

    async def find_by_platform_channel_id(
        self, session: AsyncSession, platform: PlatformORM, platform_channel_id: str
    ) -> ChannelORM | None:
        """
        플랫폼에 맞는 로직을 호출하여 채널 정보를 조회합니다.
        '총괄 매니저'는 차종(platform_code)만 확인하고, 실제 조회 작업은
        해당 차종의 전문가(logic_module)에게 위임합니다.
        """
        logic_module = self._get_logic_module(platform.platform_code)
        return await logic_module.get_by_platform_id(session, platform_channel_id)

    async def create(self, session: AsyncSession, platform: PlatformORM, dto: ChzzkChannelCreateDTO) -> ChannelORM:
        """
        플랫폼에 맞는 로직을 호출하여 새로운 채널을 생성하고 DB에 저장합니다.
        '총괄 매니저'는 트랜잭션 관리를 책임지고, 실제 객체 생성은
        전문가(logic_module)에게 위임합니다.
        """
        logic_module = self._get_logic_module(platform.platform_code)
        orm_tuple = logic_module.create_channel(platform.id, dto)
        session.add_all(orm_tuple)
        await session.flush()
        channel_orm = orm_tuple[0]
        await session.refresh(channel_orm)
        return channel_orm
