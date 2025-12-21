import xml.etree.ElementTree as ET
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import TypeVar
from urllib.parse import urljoin

import m3u8
import pydantic
from aiolimiter import AsyncLimiter
from loguru import logger

from chatzzk_clients._http.aiohttp_client import AioHTTPClient
from chatzzk_core.schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk_core.schemas.external.chzzk import (
    ChzzkAPIResponse,
    ChzzkChannelInfo,
    ChzzkVideoChat,
    ChzzkVideoChatsContent,
    ChzzkVODInfo,
    ChzzkVODMeta,
    ChzzkVODMetasContent,
)

T = TypeVar("T", bound=pydantic.BaseModel)


class ChzzkAPIClient:
    """
    Chzzk API와의 통신을 담당하는 클라이언트.
    """

    def __init__(self, config: ChzzkAPIConfig, http_client: AioHTTPClient):
        self._http_client = http_client

        self.default_headers = config.default_headers
        self.vod_manifest_headers = config.vod_mainfest_headers

        self.channel_info_url = config.channel_info_url
        self.vod_metas_url = config.vod_metas_url
        self.vod_info_url = config.vod_info_url
        self.vod_chats_url = config.vod_chats_url
        self.vod_playback_url = config.vod_playback_url

        self.page_size = config.page_size
        self.last_end_ms_offset = config.last_end_ms_offset
        self.rs_idx = config.rs_idx

        self.dash_ns = config.dash_ns

        self._proxy: str | None = config.proxy

        self._limiter = AsyncLimiter(config.rate_limit_max_rate, config.rate_limit_time_period)

    async def _fetch_content(self, url: str, model: type[T], headers: dict | None = None) -> T:
        if headers is None:
            headers = self.default_headers

        async with self._http_client.get(url, headers=headers) as response:
            data = await response.json()

            try:
                response_model = ChzzkAPIResponse[model]
                validated_response = response_model.model_validate(data)

                if validated_response.code != 200:
                    logger.error(
                        f"API Logic Error from {url}: code={validated_response.code}, msg={validated_response.message}"
                    )
                    return None

                return validated_response.content

            except pydantic.ValidationError as e:
                logger.error(f"Failed to validate response structure from {url}: {e}")
                raise

    async def fetch_channel_info(self, platform_channel_id: str) -> ChzzkChannelInfo:
        url = self.channel_info_url.format(channel_id=platform_channel_id)
        return await self._fetch_content(url, ChzzkChannelInfo)

    async def fetch_recent_vod_metas(self, platform_channel_id: str, collect_after: datetime) -> list[ChzzkVODMeta]:
        vods = []
        page = 0

        while True:
            url = self.vod_metas_url.format(channel_id=platform_channel_id, page_idx=page, page_size=self.page_size)
            response_data = await self._fetch_content(url, ChzzkVODMetasContent)

            for vod_meta in response_data.data:
                if vod_meta.publish_date < collect_after:
                    logger.info(f"Stopping fetch — VOD {vod_meta.video_no} is older than target timestamp.")
                    return vods
                vods.append(vod_meta)

            if response_data.page + 1 >= response_data.total_pages:
                break

            page += 1
        return vods

    async def fetch_vod_info(self, video_no: str) -> ChzzkVODInfo:
        url = self.vod_info_url.format(video_no=video_no)
        return await self._fetch_content(url, ChzzkVODInfo)

    async def _fetch_vod_chat_segment(self, video_no: str, player_message_time_ms: int) -> ChzzkVideoChatsContent:
        url = self.vod_chats_url.format(video_no=video_no, player_message_time=player_message_time_ms)
        async with self._limiter:
            return await self._fetch_content(url, ChzzkVideoChatsContent)

    async def _fetch_vod_chat_range_stream(
        self, video_no: str, start_time_ms: int, end_time_ms: int
    ) -> AsyncGenerator[list[ChzzkVideoChat], None]:
        player_message_time_ms = start_time_ms

        while player_message_time_ms is not None and player_message_time_ms < end_time_ms:
            try:
                vod_chats_content = await self._fetch_vod_chat_segment(video_no, player_message_time_ms)
            except Exception as e:
                logger.error(f"❌ Failed to fetch chat segment at {player_message_time_ms}ms: {e}")
                raise

            if vod_chats_content.video_chats:
                valid_chats = [c for c in vod_chats_content.video_chats if c.player_message_time <= end_time_ms]

                if valid_chats:
                    yield valid_chats

                if vod_chats_content.video_chats[-1].player_message_time > end_time_ms:
                    break

            player_message_time_ms = vod_chats_content.next_player_message_time

    async def fetch_video_chats(self, video_no: str, duration_s: int) -> AsyncGenerator[list[ChzzkVideoChat], None]:
        """
        [변경] 단일 워커 스트리밍 방식.
        전체 영상을 0초부터 끝까지 순차적으로 훑으며 데이터를 스트리밍합니다.
        """
        duration_ms = duration_s * 1000
        last_end_ms = duration_ms + self.last_end_ms_offset

        logger.info(f"🚀 Starting chat collection for video {video_no} (Duration: {duration_s}s)")

        async for chunk in self._fetch_vod_chat_range_stream(video_no, 0, last_end_ms):
            yield chunk

        logger.info(f"✅ Chat collection finished for video {video_no}")

    async def _fetch_vod_manifest_text(self, platform_video_id: str, in_key: str) -> str | None:
        url = self.vod_playback_url.format(video_id=platform_video_id, in_key=in_key)
        async with self._http_client.get(url, headers=self.vod_manifest_headers, proxy=self._proxy) as response:
            data = await response.text()
            return data

    def _parse_dash_representations(self, manifest_text: str) -> list[tuple[int, str]]:
        dash_ns = self.dash_ns
        try:
            root = ET.fromstring(manifest_text)
        except ET.ParseError as e:
            logger.error(f"Failed to parse DASH manifest: {e}")
            raise

        representations = []
        for rep in root.findall(".//mpd:Representation", namespaces=dash_ns):
            base_url_elem = rep.find("mpd:BaseURL", namespaces=dash_ns)
            if base_url_elem is not None and base_url_elem.text:
                resolution = int(rep.get("height", 0))
                if not base_url_elem.text.endswith("/hls/"):  # 플랫폼 의존
                    representations.append((resolution, base_url_elem.text))

        return representations

    async def _fetch_m3u8_url(self, m3u8_url: str) -> str:
        async with self._http_client.get(m3u8_url, headers=self.default_headers) as response:
            data = await response.text()
            return data

    async def fetch_vod_mp4_url(self, video_id: str, in_key: str):
        manifest_text = await self._fetch_vod_manifest_text(video_id, in_key)
        representations = self._parse_dash_representations(manifest_text)
        representations.sort(key=lambda x: x[0])
        target_rs_idx = max(0, min(self.rs_idx, len(representations) - 1))
        return representations[target_rs_idx][1]

    async def fetch_vod_m3u8_url(self, m3u8_url: str):
        m3u8_data = await self._fetch_m3u8_url(m3u8_url)
        m3u8_master = m3u8.loads(m3u8_data)
        representations = [
            (playlist.stream_info.resolution[1], urljoin(m3u8_url, playlist.uri)) for playlist in m3u8_master.playlists
        ]
        representations.sort(key=lambda x: x[0])
        target_rs_idx = max(0, min(self.rs_idx, len(representations) - 1))
        return representations[target_rs_idx][1]
