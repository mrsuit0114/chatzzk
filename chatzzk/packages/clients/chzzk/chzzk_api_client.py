from loguru import logger

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.schemas.config.settings import settings


class ChzzkApiClient:
    """
    Chzzk API와의 통신을 담당하는 클라이언트.
    """

    def __init__(self, http_client: BaseHttpClient):
        self._http_client = http_client
        self._proxy = settings.api.chzzk_api.https_proxy
        self._accept_headers = settings.api.chzzk_api.accept_headers

    async def get_channel_info(self, channel_id: str):
        """채널 정보를 가져옵니다."""
        url = settings.api.chzzk_api.channel_info_template.format(channel_id=channel_id)
        try:
            content = await self._http_client.get(url)
            return content
        except Exception as e:
            # loguru와 같은 로거를 사용하여 에러 로깅 필요
            logger.error(f"Error fetching channel info for {channel_id}: {e}")
            return None

    async def get_channeld_vods(self, channel_id: str, page_idx: int = 0):
        url = settings.api.chzzk_api.channel_vods_template.format(channel_id=channel_id, page_idx=page_idx)
        try:
            content = await self._http_client.get(url)
            return content
        except Exception as e:
            logger.error(f"Error fetching channel vods info for {channel_id}: {e}")
            return None

    async def get_vod_info(self, video_no: str):
        url = settings.api.chzzk_api.vod_info_template.format(video_no=video_no)
        try:
            content = await self._http_client.get(url)
            return content
        except Exception as e:
            logger.error(f"Error fetching vod info for {video_no}: {e}")
            return None

    async def get_vod_chats(self, video_no: str, next_player_message_time_ms: int):
        url = settings.api.chzzk_api.vod_chats_template.format(video_no=video_no)
        try:
            content = await self._http_client.get(url, playerMessageTime=next_player_message_time_ms)
            return content
        except Exception as e:
            logger.error(f"Error fetching chats for {video_no}: {next_player_message_time_ms}, e: {e}")
            return None

    async def get_vod_url(self, video_id: str, in_key: str):
        url = settings.api.chzzk_api.vod_url_template.format(video_id=video_id, in_key=in_key)
        try:
            content = await self._http_client.get(url, proxy=self._proxy, headers=self._accept_headers)
            return content
        except Exception as e:
            logger.error(f"Error fetching vod url for video_id={video_id}, in_key={in_key}: {e}")
            return None

    # TODO: chats의 파싱은 어디서?
