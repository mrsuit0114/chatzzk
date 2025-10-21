from typing import Any

import aiohttp
import pydantic
from loguru import logger

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.schemas.clients.chzzk import ChannelInfo
from chatzzk.packages.schemas.config.api import ChzzkApiConfig


class ChzzkApiClient:
    """
    Chzzk API와의 통신을 담당하는 클라이언트.
    """

    def __init__(self, config: ChzzkApiConfig, http_client: BaseHttpClient):
        self._http_client = http_client
        self.config = config
        self._proxy: str | None = config.https_proxy
        self._vod_manifest_headers: dict[str, str] | None = config.vod_manifest_headers

    async def fetch_channel_info(self, channel_id: str) -> ChannelInfo | None:
        """
        채널 정보를 가져옵니다.
        - 채널을 찾을 수 없는 경우(404): None을 반환합니다.
        - 그 외 모든 통신/서버 오류: 예외를 그대로 발생시킵니다.
        """
        url = self.config.channel_info_template.format(channel_id=channel_id)
        try:
            raw_content = await self._http_client.get(url)
            if raw_content is None:
                return None

            try:
                return ChannelInfo.model_validate(raw_content)
            except pydantic.ValidationError as e:
                logger.error(f"Failed to validate channel info for {channel_id}: {e}")
                raise
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"Channel not found for id: {channel_id}. Returning None.")
                return None
            logger.error(f"HTTP {e.status} error for channel {channel_id}. Re-raising exception.")
            raise
        except aiohttp.ClientError:
            logger.error(f"ClientError for channel {channel_id}. Re-raising exception.")
            raise
        except Exception:
            logger.exception(f"Unexpected error for channel {channel_id}. Re-raising exception.")
            raise

    async def get_channel_vods_info(self, channel_id: str, page_idx: int = 0) -> dict[str, Any] | None:
        """
        채널 VOD 목록 정보를 가져옵니다.
        - VOD 목록을 찾을 수 없는 경우(404): None을 반환합니다.
        - 그 외 모든 통신/서버 오류: 예외를 그대로 발생시킵니다.
        """
        url = self.config.channel_vods_info_template.format(channel_id=channel_id, page_idx=page_idx)
        try:
            content = await self._http_client.get(url)
            return content
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"Channel VODs not found for id: {channel_id} (page={page_idx}). Returning None.")
                return None
            logger.error(
                f"HTTP {e.status} error for channel VODs {channel_id} (page={page_idx}). Re-raising exception."
            )
            raise
        except aiohttp.ClientError:
            logger.error(f"ClientError for channel VODs {channel_id} (page={page_idx}). Re-raising exception.")
            raise
        except Exception:
            logger.exception(f"Unexpected error for channel VODs {channel_id} (page={page_idx}). Re-raising exception.")
            raise

    async def get_vod_info(self, video_no: str) -> dict[str, Any] | None:
        """
        VOD 상세 정보를 가져옵니다.
        - VOD를 찾을 수 없는 경우(404): None을 반환합니다.
        - 그 외 모든 통신/서버 오류: 예외를 그대로 발생시킵니다.
        """
        url = self.config.vod_info_template.format(video_no=video_no)
        try:
            content = await self._http_client.get(url)
            return content
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"VOD not found for video_no: {video_no}. Returning None.")
                return None
            logger.error(f"HTTP {e.status} error for VOD {video_no}. Re-raising exception.")
            raise
        except aiohttp.ClientError:
            logger.error(f"ClientError for VOD {video_no}. Re-raising exception.")
            raise
        except Exception:
            logger.exception(f"Unexpected error for VOD {video_no}. Re-raising exception.")
            raise

    async def get_vod_chats(self, video_no: str, next_player_message_time_ms: int) -> dict[str, Any] | None:
        """
        VOD 채팅 정보를 가져옵니다.
        - 채팅을 찾을 수 없는 경우(404): None을 반환합니다.
        - 그 외 모든 통신/서버 오류: 예외를 그대로 발생시킵니다.
        """
        url = self.config.vod_chats_template.format(video_no=video_no)
        try:
            content = await self._http_client.get(url, params={"playerMessageTime": next_player_message_time_ms})
            return content
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"VOD chats not found for video_no: {video_no}. Returning None.")
                return None
            logger.error(f"HTTP {e.status} error for VOD chats {video_no}. Re-raising exception.")
            raise
        except aiohttp.ClientError:
            logger.error(f"ClientError for VOD chats {video_no}. Re-raising exception.")
            raise
        except Exception:
            logger.exception(f"Unexpected error for VOD chats {video_no}. Re-raising exception.")
            raise

    async def get_vod_manifest(self, video_id: str, in_key: str) -> str | None:
        """
        VOD 매니페스트(HLS/DASH) 내용을 가져옵니다.
        - 매니페스트를 찾을 수 없는 경우(404): None을 반환합니다.
        - 그 외 모든 통신/서버 오류: 예외를 그대로 발생시킵니다.
        """
        url = self.config.vod_url_template.format(video_id=video_id, in_key=in_key)
        try:
            content = await self._http_client.get(
                url,
                expect_json=False,  # JSON이 아닌 텍스트 응답을 기대
                proxy=self._proxy,  # 특정 API에만 적용되는 프록시
                headers=self._vod_manifest_headers,  # 특정 API에만 적용되는 헤더
            )
            return content
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"VOD manifest not found for video_id: {video_id}. Returning None.")
                return None
            logger.error(f"HTTP {e.status} error for VOD manifest {video_id}. Re-raising exception.")
            raise
        except aiohttp.ClientError:
            logger.error(f"ClientError for VOD manifest {video_id}. Re-raising exception.")
            raise
        except Exception:
            logger.exception(f"Unexpected error for VOD manifest {video_id}. Re-raising exception.")
            raise
