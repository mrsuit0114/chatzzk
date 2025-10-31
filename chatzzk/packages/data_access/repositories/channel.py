# 여기서 ORM을 제공함으로서 서비스에서는 세션을 한번 열었을 때 원자성을 보장할 수 있음
# 에그리거트를 관리함 - llm_meta_data는 채널에 종속적이기 때문에 따로 레포지토리를 구현하지 않고 channel에서 관리함

from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.logics.channel_base import ChannelLogicBase
from chatzzk.packages.schemas.dto.repo_params.core.channel import ChannelCreateParams, ChannelFindParams
from chatzzk.packages.schemas.orm.models import ChannelORM


class ChannelRepository:
    def __init__(self, channel_logic_factory: dict[PlatformCode, ChannelLogicBase]):
        self.factory = channel_logic_factory

    def _get_logic(self, platform_code: PlatformCode):
        logic_module = self.factory.get(platform_code)
        if logic_module:
            return logic_module
        else:
            raise ValueError(f"No logic module found for platform_code: {platform_code}")

    async def create_channel(
        self, session: AsyncSession, platform_code: PlatformCode, params: ChannelCreateParams
    ) -> ChannelORM:
        logic_module = self._get_logic(platform_code)
        return await logic_module.create_channel(session, params)

    async def find_channel(
        self, session: AsyncSession, platform_code: PlatformCode, params: ChannelFindParams
    ) -> ChannelORM:
        logic_module = self._get_logic(platform_code)
        return await logic_module.find_channel(session, params)
