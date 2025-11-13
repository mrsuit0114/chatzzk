from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.schemas.dto.repo_params.core.vod import VODCreateParams, VODFindParams
from chatzzk.packages.schemas.orm.models import VOD


class VODLogicBase(Protocol):
    def create_platform_vod(self, session: AsyncSession, params: VODCreateParams) -> VOD: ...

    async def find_vod_with_platform_vod(self, session: AsyncSession, params: VODFindParams) -> VOD: ...
