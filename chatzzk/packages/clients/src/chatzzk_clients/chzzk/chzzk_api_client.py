import asyncio
import xml.etree.ElementTree as ET
from collections import deque
from urllib.parse import urljoin

import m3u8
import pydantic
from loguru import logger

from chatzzk_clients._http.aiohttp_client import AioHTTPClient
from chatzzk_schemas.api_models.chzzk import (
    ChzzkChannelInfo,
    ChzzkChannelVODs,
    ChzzkVideoChat,
    ChzzkVODChats,
    ChzzkVODInfo,
    ChzzkVODMeta,
)
from chatzzk_schemas.config.clients.chzzk import ChzzkAPIConfig


class ChzzkAPIClient:
    """
    Chzzk API와의 통신을 담당하는 클라이언트.
    """

    def __init__(self, config: ChzzkAPIConfig, http_client: AioHTTPClient):
        self._http_client = http_client

        self.default_headers = config.default_headers
        self.vod_manifest_headers = config.vod_mainfest_headers

        self.channel_info_url = config.channel_info_url
        self.channel_vods_url = config.channel_vods_url
        self.vod_info_url = config.vod_info_url
        self.vod_chats_url = config.vod_chats_url
        self.vod_playback_url = config.vod_playback_url

        self.page_size = config.page_size
        self.worker_num = config.worker_num
        self.last_end_ms_offset = config.last_end_ms_offset
        self.rs_idx = config.rs_idx

        self.dash_ns = config.dash_ns

        self._proxy: str | None = config.proxy
        # self._vod_manifest_headers: dict[str, str] | None = config.vod_manifest_headers

    async def fetch_channel_info(self, platform_channel_id: str) -> ChzzkChannelInfo:
        url = self.channel_info_url.format(channel_id=platform_channel_id)
        async with self._http_client.get(url, headers=self.default_headers) as response:
            data = await response.json()
            content = data.get("content")

            try:
                return ChzzkChannelInfo.model_validate(content)
            except pydantic.ValidationError as e:
                logger.error(f"Failed to validate channel info for {platform_channel_id}: {e}")
                raise

    async def fetch_channel_vod_metas(
        self, platform_channel_id: str, collect_after_timestamp_ms: int
    ) -> list[ChzzkVODMeta]:
        vods: list[ChzzkVODMeta] = []
        page = 0

        while True:
            url = self.channel_vods_url.format(channel_id=platform_channel_id, page_idx=page, page_size=self.page_size)
            async with self._http_client.get(url, headers=self.default_headers) as response:
                data = await response.json()
                content = data.get("content")

            try:
                response_data = ChzzkChannelVODs.model_validate(content)
            except pydantic.ValidationError as e:
                logger.error(f"Failed to validate VOD list for channel {platform_channel_id}: {e}")
                raise

            for vod_meta in response_data.data:
                if vod_meta.publish_date_at < collect_after_timestamp_ms:
                    logger.info(f"Stopping fetch — VOD {vod_meta.video_no} is older than target timestamp.")
                    return vods
                vods.append(vod_meta)

            if response_data.page + 1 >= response_data.total_pages:
                break

            page += 1
        return vods

    async def fetch_vod_info(self, video_no: int) -> ChzzkVODInfo:
        url = self.vod_info_url.format(video_no=video_no)
        async with self._http_client.get(url, headers=self.default_headers) as response:
            data = await response.json()
            content = data.get("content")

        try:
            return ChzzkVODInfo.model_validate(content)
        except pydantic.ValidationError as e:
            logger.error(f"Failed to validate vod info for {video_no}: {e}")
            raise

    async def _fetch_vod_chat_segment(self, video_no: int, player_message_time_ms: int) -> ChzzkVODChats:
        url = self.vod_chats_url.format(video_no=video_no, player_message_time=player_message_time_ms)
        async with self._http_client.get(url, headers=self.default_headers) as response:
            data = await response.json()
            content = data.get("content")

            try:
                return ChzzkVODChats.model_validate(content)
            except pydantic.ValidationError as e:
                logger.error(f"Failed to validate vod info for {video_no}: {e}")
                raise

    async def _fetch_vod_chat_range(self, video_no: int, start_time_ms: int, end_time_ms: int) -> deque[ChzzkVideoChat]:
        player_message_time_ms = start_time_ms
        collected: deque[ChzzkVideoChat] = deque()

        while player_message_time_ms is not None and player_message_time_ms < end_time_ms:
            vod_chats_content = await self._fetch_vod_chat_segment(video_no, player_message_time_ms)
            collected.extend(vod_chats_content.video_chats)
            player_message_time_ms = vod_chats_content.next_player_message_time

        while collected and collected[-1].player_message_time > end_time_ms:
            collected.pop()

        return collected

    async def fetch_vod_chats(self, video_no: int, duration_s: int) -> deque[ChzzkVideoChat]:
        duration_ms = duration_s * 1000
        last_end_ms = duration_ms + self.last_end_ms_offset
        worker_num = self.worker_num

        segment_size = duration_ms // worker_num
        semaphore = asyncio.Semaphore(worker_num)
        tasks = []

        async def worker(start_ms: int, end_ms: int | None) -> deque[ChzzkVideoChat]:
            async with semaphore:
                return await self._fetch_vod_chat_range(video_no, start_ms, end_ms)

        for i in range(worker_num):
            start_ms = i * segment_size
            end_ms = (i + 1) * segment_size if i < worker_num - 1 else last_end_ms
            tasks.append(worker(start_ms, end_ms))

        segments = await asyncio.gather(*tasks)
        merged = deque()
        for segment in segments:
            merged.extend(segment)

        return merged

    async def _fetch_vod_manifest_text(self, platform_video_id: str, in_key: str) -> str | None:
        url = self.vod_playback_url.format(video_id=platform_video_id, in_key=in_key)
        async with self._http_client.get(url, headers=self.vod_manifest_headers, proxy=self._proxy) as response:
            data = await response.text()
            return data

    def _parse_dash_representations(self, manifest_text: str) -> list[tuple[int, str]]:
        dash_ns = self.dash_ns
        root = ET.fromstring(manifest_text)

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
