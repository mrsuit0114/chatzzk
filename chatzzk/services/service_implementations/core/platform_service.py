from loguru import logger

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.platform import PlatformRepository
from chatzzk.packages.schemas.orm.models import PlatformORM


class PlatformService:
    def __init__(self, platform_repo: PlatformRepository):
        self.platform_repo = platform_repo

    def add_platform(self, platform_code: PlatformCode, platform_name: str, donation_unit: str) -> PlatformORM:
        """
        새로운 플랫폼을 DB에 등록하거나, 이미 존재하면 기존 정보를 반환합니다.
        """
        logger.info(f"Attempting to add platform: {platform_name}")
        existing = self.platform_repo.find_by_code(platform_code)
        if existing:
            logger.info(f"Already existing platform: {platform_code.value}")
            return existing
        return self.platform_repo.create(platform_code, platform_name, donation_unit)

    def get_platform_by_code(self, platform_code: PlatformCode) -> PlatformORM | None:
        return self.channel_repo.get_platform_by_code(platform_code)
