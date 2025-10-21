from typing import Protocol


class ChannelManagement(Protocol):
    """
    수집 대상인 '채널'을 관리하는 책임을 정의합니다.
    """

    async def add_channel(self, platform_channel_id: str) -> int:
        """
        플랫폼 고유 ID를 사용하여 새로운 채널을 DB에 등록하고,
        시스템의 통합 channel_id를 반환합니다.
        이미 존재하는 채널이라면 기존 channel_id를 반환합니다.
        """
        ...

    def sync_channel_info(self, channel_id: int) -> None:
        """
        DB에 저장된 채널의 메타데이터(채널명, 프로필 사진 등)를
        플랫폼의 최신 정보와 동기화합니다.
        """
        ...

    def set_collection_policy(self, channel_id: int, allow_collection: bool) -> None:
        """
        특정 채널의 데이터 수집 정책(수집 허용 여부 등)을 설정합니다.
        """
        ...
