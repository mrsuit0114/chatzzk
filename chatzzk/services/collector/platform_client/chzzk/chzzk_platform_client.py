# 스트리머 ID를 받아서 video_num 목록을 반환
# video_num을 받아 mp4 다운로드 url을 반환 - 프록시 필요
# video_num을 받아 채팅 내역을 크롤링

# services/collector/platform_client/chzzk_platform_client.py
# video_num은 수치가 아니라 식별자로서 동작하기 때문에 str 힌팅 사용

import json
import os
import random
import time

import requests
from chatzzk.packages.schemas.data_models import VodContextEntry
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

        self.vod_url_template = chzzk_api_settings.CHZZK_VOD_URL_TEMPLATE
        self.vod_info_url_template = chzzk_api_settings.CHZZK_VOD_INFO_URL_TEMPLATE
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

    def get_video_nums(self, streamer_id: str) -> list[str]:
        """스트리머 ID를 받아서 video_num 목록을 반환"""
        # TODO 크롤링해서 가져오는 함수 구현
        return ["video1", "video2"]

    def get_download_url(self, video_num: str) -> str:
        """video_num을 받아 mp4 다운로드 url을 반환 (프록시 사용)"""
        return "http://example.com/video.mp4"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random(min=1, max=2),
        before_sleep=_log_before_retry,  # 재시도 전 로깅 콜백 추가
    )
    def _request_chats(self, url: str, player_message_time: int) -> dict:
        """
        재시도 메커니즘을 포함하여 채팅 데이터를 요청합니다.
        HTTP 오류, 빈 응답, JSON 파싱 오류 시 예외를 발생시켜 재시도합니다.
        """
        params = {"playerMessageTime": player_message_time}

        # requests.RequestException은 ConnectionError, Timeout 등을 모두 포함
        # json.JSONDecodeError도 함께 처리하여 깨진 JSON 응답에도 재시도
        try:
            response = self.session.get(url, params=params, timeout=10)  # 타임아웃 추가
            response.raise_for_status()  # 4xx, 5xx 에러 발생 시 HTTPError (RequestException의 서브클래스)
            data = response.json()

            if not data or not data.get("content"):
                # 응답은 왔지만 내용이 비어있는 경우도 재시도 대상에 포함
                raise ValueError("Empty or invalid content in response data")

            return data
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError) as e:
            # tenacity가 이 예외들을 잡아서 재시도하게 하려면 다시 raise 해야 함
            raise e

    def _parse_video_chats(self, data) -> tuple[list[VodContextEntry], int]:
        content = data.get("content")
        if not content:
            logger.error(f"❌ No content found in data: {data}")
            raise ValueError(f"No content found in data: {data}")

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

    def crawl_chat(self, video_num: str) -> list[VodContextEntry]:
        all_contexts = []
        next_player_message_time = 0
        chat_url = self.vod_chat_url_template.format(video_num=video_num)

        while next_player_message_time is not None:
            try:
                # 재시도 로직이 포함된 _request_chats를 호출
                data = self._request_chats(chat_url, next_player_message_time)

                # 데이터가 성공적으로 받아와진 경우에만 파싱 진행
                video_chats, next_player_message_time = self._parse_video_chats(data)

                if video_chats:
                    all_contexts.extend(video_chats)

                logger.info(f"next_player_message_time: {next_player_message_time}")

                # 다음 요청까지 대기
                time.sleep(BASE_SLEEP_TIME * random.uniform(0.5, 1.5))

            except requests.exceptions.RequestException as e:
                # tenacity의 모든 재시도가 실패한 경우 (네트워크/API 문제)
                logger.error(f"❌ API request failed after all retries for video {video_num}: {e}")
                raise RuntimeError(f"API request failed for {video_num}") from e

            except ValueError as e:
                # _parse_video_chats에서 응답 형식이 깨진 경우 (파싱 문제)
                logger.error(f"❌ Failed to parse response for video {video_num}: {e}")
                raise RuntimeError(f"Response parsing failed for {video_num}") from e

        logger.info(f"🎉 Successfully crawled {len(all_contexts)} chats for video {video_num}.")

        return all_contexts


if __name__ == "__main__":
    VIDEO_NUM = 8929780
    chzzk_platform_client = ChzzkPlatformClient()

    chat_data = chzzk_platform_client.crawl_chat(VIDEO_NUM)

    logger.info("crawling fin")
