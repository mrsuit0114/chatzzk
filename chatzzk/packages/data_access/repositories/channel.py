from sqlalchemy.orm import Session, sessionmaker

from chatzzk.packages.schemas.orm.models import ChannelORM, PlatformORM

from . import chzzk_channel_logic
from .channel_logic_interface import ChannelLogicInterface


class ChannelRepository:
    """플랫폼 중립적인 채널 애그리거트 데이터 접근을 캡슐화합니다."""

    def __init__(self, db_session_factory: sessionmaker[Session]):
        self.db_session_factory = db_session_factory
        # 플랫폼 코드와 해당 플랫폼의 로직 모듈을 매핑하는 레지스트리
        # 타입 힌트를 통해 모든 로직 모듈이 인터페이스를 준수함을 명시
        self.logic_registry: dict[str, ChannelLogicInterface] = {
            "chzzk": chzzk_channel_logic,
            # "youtube": youtube_channel_logic, # 유튜브 추가 시 등록
        }

    def get_by_platform_id(self, platform_code: str, platform_channel_id: str) -> ChannelORM | None:
        """
        플랫폼에 맞는 로직을 호출하여 채널 정보를 조회합니다.
        """
        logic_module = self.logic_registry.get(platform_code)
        if not logic_module:
            raise ValueError(f"Unsupported platform code: {platform_code}")

        with self.db_session_factory() as session:
            return logic_module.get_by_platform_id(session, platform_channel_id)

    def create(self, platform: PlatformORM, **kwargs) -> ChannelORM:
        """
        플랫폼에 맞는 로직을 호출하여 새로운 채널을 생성하고 DB에 저장합니다.
        트랜잭션 관리를 책임집니다.
        """
        logic_module = self.logic_registry.get(platform.platform_code)
        if not logic_module:
            raise ValueError(f"Unsupported platform code: {platform.platform_code}")

        with self.db_session_factory() as session:
            try:
                # 1. 실제 객체 생성은 로직 모듈에 위임
                new_channel = logic_module.create(session, platform, **kwargs)

                # 2. 트랜잭션 커밋
                session.commit()

                # 3. DB의 최신 정보로 객체 새로고침
                session.refresh(new_channel)

                return new_channel
            except Exception:
                session.rollback()
                raise
