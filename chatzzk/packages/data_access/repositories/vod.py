from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.logics.vod_base import VODLogicBase
from chatzzk.packages.schemas.dto.repo_params.core.vod import VODCreateParams
from chatzzk.packages.schemas.orm.models import VOD


class VODRepository:
    def __init__(self, vod_logic_factory: dict[PlatformCode, VODLogicBase]):
        self.factory = vod_logic_factory

    def _get_logic(self, platform_code: PlatformCode):
        logic_module = self.factory.get(platform_code)
        if logic_module:
            return logic_module
        else:
            raise ValueError(f"No logic module found for platform_code: {platform_code}")

    def create_platform_vod(self, session: AsyncSession, platform_code: PlatformCode, params: VODCreateParams) -> VOD:
        logic_module = self._get_logic(platform_code)
        return logic_module.create_platform_vod(session, params)
