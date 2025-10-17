from sqlalchemy.orm import Session, sessionmaker

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.orm.models import PlatformORM


class PlatformRepository:
    def __init__(self, db_session_factory: sessionmaker[Session]):
        self.db_session_factory = db_session_factory

    def find_by_code(self, platform_code: PlatformCode) -> PlatformORM | None:
        with self.db_session_factory() as session:
            return session.query(PlatformORM).filter_by(platform_code=platform_code).first()

    def create(self, platform_code: PlatformCode, platform_name: str, donation_unit: str) -> PlatformORM:
        with self.db_session_factory() as session:
            new_platform = PlatformORM(
                platform_code=platform_code,
                platform_name=platform_name,
                donation_unit=donation_unit,
            )
            session.add(new_platform)
            session.commit()
            session.refresh(new_platform)
            return new_platform
