from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.schemas.dto.repo_params.core.vod import VODCreateParams
from chatzzk.packages.schemas.orm.models import VOD


class VODLogicBase(Protocol):
    async def create_platform_vod(self, session: AsyncSession, params: VODCreateParams) -> VOD: ...
