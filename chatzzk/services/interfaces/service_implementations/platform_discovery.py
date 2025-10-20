from typing import Protocol

# --- Flow 1: Discovery ---


class PlatformDiscovery(Protocol):
    """
    플랫폼의 채널 및 VOD를 '발견(Discovery)'하는 역할을 정의합니다.
    어떤 채널을 수집할지, 어떤 VOD가 새로운 것인지 식별하는 탐색 작업을 책임집니다.
    주로 주기적인 스케줄링을 통해 실행됩니다.
    """

    def discover_new_vods(self, channel_id: int) -> list[str]:
        """
        특정 채널의 신규 VOD를 탐색하고 데이터베이스에 기록합니다.
        새롭게 발견되어 처리가 필요한 VOD들의 video_no 리스트를 반환합니다.
        """
        ...
