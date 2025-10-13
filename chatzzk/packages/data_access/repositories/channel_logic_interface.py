from typing import Protocol

from sqlalchemy.orm import Session

from chatzzk.packages.schemas.orm.models import ChannelORM, PlatformORM


class ChannelLogicInterface(Protocol):
    """
    각 플랫폼별 채널 로직 모듈이 반드시 구현해야 하는 함수들의 인터페이스를 정의합니다.
    """

    def get_by_platform_id(self, session: Session, platform_channel_id: str) -> ChannelORM | None:
        """플랫폼 고유 ID로 채널 정보를 조회합니다."""
        ...

    def create(self, session: Session, platform: PlatformORM, **kwargs) -> ChannelORM:
        """새로운 채널과 관련 객체들을 생성합니다."""
        ...
