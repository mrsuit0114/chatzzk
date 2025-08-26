# 스트리머 ID를 받아서 video_no 목록을 반환
# video_no을 받아 mp4 다운로드 url을 반환 - 프록시 필요
# video_no을 받아 채팅 내역을 크롤링

# services/collector/platform_client/chzzk_platform_client.py
# video_no은 수치가 아니라 식별자로서 동작하기 때문에 str 힌팅 사용

import json
import os
import random
import time

import requests
from chatzzk.packages.schemas.data_models import VodContextEntry
from chatzzk.packages.utils.file_io import load_json_from_file
from chatzzk.services.collector.settings import chzzk_api_settings
from chzzk_constants import CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_random

BASE_SLEEP_TIME = 1


def _log_before_retry(retry_state):
    logger.warning(
        f"Retrying request due to {retry_state.outcome.exception()}, attempt #{retry_state.attempt_number}..."
    )


class ChzzkPlatformClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": chzzk_api_settings.USER_AGENT})

        self._cookies = None
        self.cookies_file_path = chzzk_api_settings.CHZZK_COOKIES_FILE_PATH

        self.vod_url_template = chzzk_api_settings.CHZZK_VOD_URL_TEMPLATE
        self.vod_info_url_template = chzzk_api_settings.CHZZK_VOD_INFO_URL_TEMPLATE
        self.channel_vods_url_template = chzzk_api_settings.CHZZK_CHANNEL_VODS_URL_TEMPLATE

        self.vod_chat_url_template = chzzk_api_settings.CHZZK_VOD_CHAT_URL_TEMPLATE
        # --- 프록시 설정 부분 ---
        self.proxies = None
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")

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

    def get_video_info(self, channel_id: str) -> list[str]:
        try:
            api_url = self.channel_vods_url_template.format(channel_id=channel_id)
            content = self._api_request(url=api_url, requires_auth=True)

            # videoId 리스트 추출
            video_ids = [video["videoNo"] for video in content.get("data", [])]
            # 필요한 정보를 여기서 다 추출할 것 - VideoInfo
            # videoNo, videoId, videoTitle, publishData, duration, readCount, publishDateAt, categoryType, videoCategory(게임 이름 영문), videoCategoryValue(게임 이름 한글)
            # exposure, adult,

            return video_ids
        except (ConnectionError, ValueError, requests.RequestException) as e:
            logger.error(f"❌ 최종적으로 비디오 정보 획득 실패: {e}")
            return []

    def get_download_url(self, video_no: str) -> str:
        """video_no을 받아 mp4 다운로드 url을 반환 (프록시가 있으면 프록시 사용)"""
        return "http://example.com/video.mp4"

    def _parse_video_chats(self, content: dict) -> tuple[list[VodContextEntry], int]:
        next_player_message_time = content.get("nextPlayerMessageTime")
        video_chats = content.get("videoChats")

        if not video_chats:
            logger.info("No new chats in this response.")
            return [], next_player_message_time

        result: list[VodContextEntry] = []

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
                VodContextEntry(
                    timestamp_ms=timestamp_ms,
                    type=context_type,
                    content=chat_content,
                    pay_amount=pay_amount,
                )
            )

        return result, next_player_message_time

    def crawl_chat(self, video_no: str) -> list[VodContextEntry]:
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


if __name__ == "__main__":
    VIDEO_NO = 8929780
    CHANNEL_ID = "f39c3d74e33a81ab3080356b91bb8de5"
    chzzk_platform_client = ChzzkPlatformClient()

    chat_contexts = chzzk_platform_client.crawl_chat(VIDEO_NO)
    video_ids = chzzk_platform_client.get_video_info(CHANNEL_ID)

    cookies = chzzk_platform_client._get_cookies()

    logger.info("crawling fin")
