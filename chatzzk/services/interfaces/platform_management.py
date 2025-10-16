from typing import Protocol


class PlatformManagement(Protocol):
    """
    데이터 수집 파이프라인 자체와는 별개로,
    수집 대상(채널)을 관리하는 데 필요한 기능을 정의합니다.
    주로 관리자 도구나 수동 스크립트를 통해 사용됩니다.
    """

    def sync_channel_info(self, channel_id: int) -> None:
        """
        DB에 저장된 채널의 메타데이터(채널명, 프로필 사진 등)를
        플랫폼의 최신 정보와 동기화합니다.
        """
        ...

    def add_new_channel(self, platform_channel_id: str) -> int:
        """
        플랫폼 고유 ID를 사용하여 새로운 채널을 DB에 등록하고,
        시스템 내부의 channel_id를 반환합니다.
        이미 존재하는 채널이라면 기존 channel_id를 반환합니다.
        """
        ...
