from .._http.client import BaseHttpClient
from .dto import ChzzkChannelInfo


class ChzzkApiClient(BaseHttpClient):
    """
    Chzzk API와의 통신을 담당하는 클라이언트.
    """

    CHZZK_API_URL = "https://api.chzzk.naver.com"

    async def get_channel_info(self, channel_id: str) -> ChzzkChannelInfo | None:
        """채널 정보를 가져옵니다."""
        url = f"{self.CHZZK_API_URL}/service/v1/channels/{channel_id}"
        try:
            content_dict = await self._request("GET", url)
            if content_dict:
                return ChzzkChannelInfo.model_validate(content_dict)
        except Exception as e:
            # loguru와 같은 로거를 사용하여 에러 로깅 필요
            print(f"Error fetching channel info for {channel_id}: {e}")
            return None

    # TODO: VOD 목록, VOD 상세 정보, 채팅 등 다른 API 메소드들을 여기에 구현 예정
