# 스트리머 ID를 받아서 video_no 목록을 반환
# video_no을 받아 mp4 다운로드 url을 반환 - 프록시 필요
# video_no을 받아 채팅 내역을 크롤링

# services/collector/platform_client/chzzk_platform_client.py
# video_no은 수치가 아니라 식별자로서 동작하기 때문에 str 힌팅 사용

import json
import os
import random
import time
import xml.etree.ElementTree as ET
from collections.abc import Generator

import requests
from loguru import logger
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_random

from chatzzk.packages.schemas.data_models import ChzzkVod, StreamContextEntry
from chatzzk.packages.utils.file_io import load_json_from_file
from chatzzk.services.collector.platform_client.chzzk.chzzk_constants import (
    CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE,
)
from chatzzk.services.collector.settings import collector_settings

BASE_SLEEP_TIME = 0.5


def _log_before_retry(retry_state):
    logger.warning(
        f"Retrying request due to {retry_state.outcome.exception()}, attempt #{retry_state.attempt_number}..."
    )


class ChzzkPlatformClient:
    DASH_NS = {"mpd": "urn:mpeg:dash:schema:mpd:2011"}

    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False  # 의도한 API호출에서만(vod_url) 프록시 사용
        self.session.headers.update({"User-Agent": collector_settings.chzzk_api.user_agent})

        self._cookies = None
        self.cookies_file_path = collector_settings.chzzk_api.cookies_file_path

        self.vod_url_template = collector_settings.chzzk_api.vod_url_template
        self.vod_info_url_template = collector_settings.chzzk_api.vod_info_url_template
        self.channel_vods_url_template = collector_settings.chzzk_api.channel_vods_url_template

        self.vod_chat_url_template = collector_settings.chzzk_api.vod_chat_url_template
        # --- 프록시 설정 부분 ---
        self.proxies = None
        http_proxy = os.getenv("MY_HTTP_PROXY")
        https_proxy = os.getenv("MY_HTTPS_PROXY")

        # 환경 변수가 설정되어 있을 경우에만 프록시를 사용
        if http_proxy or https_proxy:
            self.proxies = {
                "http": http_proxy,
                "https": https_proxy,
            }
            logger.info(f"Proxy is enabled: {self.proxies}")
        else:
            logger.info("Proxy is not configured.")

    def _get_cookies(self) -> dict | None:
        if not self._cookies and self.cookies_file_path:
            self._cookies = load_json_from_file(self.cookies_file_path)

        return self._cookies

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2), before_sleep=_log_before_retry)
    def _api_request(self, url: str, params: dict = None, requires_auth: bool = False) -> dict:
        """
        모든 API 요청을 처리하는 중앙 핸들러. 재시도, 인증, 응답 검증을 책임집니다.
        성공 시 항상 검증된 'content' 딕셔너리를 반환합니다.
        """
        kwargs = {"params": params, "timeout": 10}

        # 인증이 필요하면, 쿠키를 kwargs에 추가
        if requires_auth:
            cookies = self._get_cookies()
            if cookies:
                kwargs["cookies"] = cookies
            # 쿠키가 없어도 일단 요청은 시도해볼 수 있음 (공개 VOD 등)

        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            data = response.json()

            content = data.get("content")
            if content:  # content가 존재하고 비어있지 않은 경우
                return content

            # content가 없는 것은 API 레벨의 오류로 간주하고 재시도 유발
            raise ValueError(f"API response from {url} is missing 'content' key.")

        except (requests.RequestException, json.JSONDecodeError) as e:
            # 이 예외들은 tenacity가 잡아서 재시도를 수행하게 됨
            raise e

    # mp4 url획득이나 liveOpenDate에 대한 정보가 필요하기 때문에 다른 api에 요청이 필요함 여기서는 모든 no만 반환할 것
    def stream_all_video_numbers(self, channel_id: str) -> Generator[str, None, None]:
        """
        특정 채널의 모든 VOD 번호('video_no')를 스트리밍(yield)합니다.
        API 통신 실패 시 스트리밍을 중단합니다.
        """
        page_idx = 0
        while True:
            try:
                api_url = self.channel_vods_url_template.format(channel_id=channel_id, page_idx=page_idx)
                content = self._api_request(url=api_url, requires_auth=True)

                videos_data = content.get("data", [])
                if not videos_data:
                    logger.info(f"No more VODs found for channel {channel_id} at page {page_idx}.")
                    break

                logger.info(f"Streaming {len(videos_data)} VOD numbers from page {page_idx}.")
                for video in videos_data:
                    if video_no := video.get("videoNo"):  # Walrus operator (Python 3.8+)
                        yield str(video_no)

                page_idx += 1
                time.sleep(BASE_SLEEP_TIME)

            except (ConnectionError, ValueError) as e:
                logger.error(f"Failed to fetch VOD list for channel {channel_id} at page {page_idx}: {e}")
                break

    def fetch_vod_details(self, video_no: str) -> tuple[ChzzkVod, str, str] | None:
        """
        특정 VOD의 상세 정보와 재생 키를 가져옵니다.
        어떤 종류의 실패든 항상 None을 반환하도록 통일합니다.
        """
        api_url = self.vod_info_url_template.format(video_no=video_no)
        try:
            content = self._api_request(url=api_url, requires_auth=True)

            # 1. Pydantic의 자동 파싱/검증 기능을 최대한 활용
            vod_info = ChzzkVod.model_validate(content)

            # 2. 필수 키 존재 여부 확인
            video_id = content.get("videoId")
            in_key = content.get("inKey")

            if not (video_id and in_key):
                logger.error(f"Missing videoId or inKey for video_no {video_no}")
                return None

            return vod_info, video_id, in_key

        except ValidationError as e:
            # Pydantic 모델 검증 실패 시 (필수 필드 누락, 타입 불일치 등)
            logger.error(f"Failed to parse/validate VOD info for {video_no}: {e}")
            return None
        except (ConnectionError, ValueError) as e:
            # 네트워크 오류 또는 _api_request 실패 시
            logger.error(f"Failed to fetch VOD details for {video_no}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2), before_sleep=_log_before_retry)
    def fetch_all_stream_representations(self, video_id: str, in_key: str) -> list[tuple[int, str]] | None:
        """
        DASH manifest를 파싱하여 사용 가능한 모든 스트림 표현(해상도, URL)의 리스트를 반환합니다.
        제공받는 url의 안전성을 위해 프록시를 사용합니다.
        리스트는 해상도 오름차순으로 정렬됩니다.
        """
        if not (video_id and in_key):
            logger.warning("video_id and in_key are required to fetch stream URL.")
            return None

        playback_url = self.vod_url_template.format(video_id=video_id, in_key=in_key)

        try:
            # self.session 사용 및 proxies, timeout 적용
            response = self.session.get(
                playback_url,
                headers={"Accept": "application/dash+xml"},
                proxies=self.proxies,  # 프록시 적용
                timeout=10,
            )
            response.raise_for_status()
            manifest_text = response.text
            root = ET.fromstring(manifest_text)

            representations = []
            for rep in root.findall(".//mpd:Representation", namespaces=self.DASH_NS):
                base_url_elem = rep.find("mpd:BaseURL", namespaces=self.DASH_NS)
                if base_url_elem is not None and base_url_elem.text:
                    resolution = int(rep.get("height", 0))
                    if not base_url_elem.text.endswith("/hls/"):
                        representations.append((resolution, base_url_elem.text))

            if not representations:
                logger.warning(f"No valid stream representations found for video_id {video_id}")
                return []  # 유효한 스트림이 없는 것은 오류가 아니므로, 빈 리스트 반환

            # 해상도 오름차순으로 정렬하여 반환
            representations.sort(key=lambda x: x[0])

            logger.info(f"🔗 Found {len(representations)} stream representations for video_id {video_id}.")
            return representations

        except requests.RequestException as e:
            logger.error(f"Failed to fetch DASH manifest for video_id {video_id}: {e}")
            raise e  # tenacity가 재시도하도록 다시 raise
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML manifest for video_id {video_id}: {e}")
            # XML 파싱 실패는 심각한 오류이므로 None 반환 (또는 예외 발생)
            return None

    def _parse_video_chats(self, content: dict) -> tuple[list[StreamContextEntry], int]:
        next_player_message_time = content.get("nextPlayerMessageTime")
        video_chats = content.get("videoChats")

        if not video_chats:
            logger.info("No new chats in this response.")
            return [], next_player_message_time

        result: list[StreamContextEntry] = []

        for chat in video_chats:
            msg_type_code = chat.get("messageTypeCode")
            context_type = CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE.get(msg_type_code)
            if context_type is None:
                logger.warning(f"⚠️ Unhandled messageTypeCode '{msg_type_code}' found. Skipping this chat. Data: {chat}")
                continue

            timestamp_ms = chat.get("playerMessageTime")
            chat_content = chat.get("content", "")
            extras = chat.get("extras")
            pay_amount = 0
            if extras:
                try:
                    extras_dict = json.loads(extras)
                    pay_amount = extras_dict.get("payAmount", 0)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse extras: {extras} ({e})")

            result.append(
                StreamContextEntry(
                    timestamp_ms=timestamp_ms,
                    type=context_type,
                    content=chat_content,
                    pay_amount=pay_amount,
                )
            )

        return result, next_player_message_time

    def crawl_chat(self, video_no: str) -> list[StreamContextEntry]:
        all_contexts = []
        next_player_message_time = 0
        chat_url = self.vod_chat_url_template.format(video_no=video_no)

        while next_player_message_time is not None:
            try:
                params = {"playerMessageTime": next_player_message_time}
                content = self._api_request(url=chat_url, params=params)

                # 데이터가 성공적으로 받아와진 경우에만 파싱 진행
                video_chats, next_player_message_time = self._parse_video_chats(content)

                if video_chats:
                    all_contexts.extend(video_chats)

                logger.info(f"next_player_message_time: {next_player_message_time}")
                time.sleep(BASE_SLEEP_TIME * random.uniform(0.5, 1.5))

            except requests.exceptions.RequestException as e:
                # tenacity의 모든 재시도가 실패한 경우 (네트워크/API 문제)
                logger.error(f"❌ API request failed after all retries for video {video_no}: {e}")
                raise RuntimeError(f"API request failed for {video_no}") from e

            except ValueError as e:
                # _parse_video_chats에서 응답 형식이 깨진 경우 (파싱 문제)
                logger.error(f"❌ Failed to parse response for video {video_no}: {e}")
                raise RuntimeError(f"Response parsing failed for {video_no}") from e

        logger.success(f"🎉 Successfully crawled {len(all_contexts)} chats for video {video_no}.")

        return all_contexts
