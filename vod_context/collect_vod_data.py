# curl -L "https://a01-g-naver-vod.akamaized.net/glive/c/read/v2/VOD_ALPHA/glive/23547D8571C7B393BF03DD3142CA9DE6B5A5/pd/1748223611435/a5ccc0ec-39d2-11f0-9514-b4432650023e.mp4?__gda__=1749727258_dde9059968da256f24a0d3c7f2130452" -o "./data/videos/output.mp4"
# ffmpeg -i ./data/videos/output.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 ./data/audios/output.wav
# crawl chat

import json
import random
import time
from typing import Any, Optional

import requests
from loguru import logger

VIDEOCHATS_BASE_URL = "https://api.chzzk.naver.com/service/v1/videos"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)

PROMPT_CMD_TO_TYPE_CODE = {"chat": 100, "donation": 1000, "asr": 10000}


def _get_chats_url_of_video_id(video_id: int) -> str:
    return f"{VIDEOCHATS_BASE_URL}/{video_id}/chats"


def _get_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def _request_chzzk_chats(video_id: int, player_message_time: int) -> Optional[dict[str, Any]]:
    url = _get_chats_url_of_video_id(video_id)
    params = {"playerMessageTime": player_message_time}

    try:
        response = requests.get(url, headers=_get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        return None


def crawl_chat_data_for_video(video_id: int, base_sleep_time: float = 0.5):
    next_player_message_time = 0
    retry_count = 0
    max_retries = 3

    while next_player_message_time is not None:
        try:
            data = _request_chzzk_chats(video_id, next_player_message_time)
            if not data:
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"Retrying ({retry_count}/{max_retries}) for video_id: {video_id}")
                    continue
                logger.error(f"❌ Failed to crawl chat data for video_id: {video_id} after {max_retries} retries")
                return False

            video_chats, next_player_message_time = _parse_video_chats(data)
            _append_chats_to_jsonl(video_chats, video_id)
            retry_count = 0  # Reset retry count on success
            time.sleep(base_sleep_time * random.uniform(0.5, 1.5))
        except Exception as e:
            logger.error(f"❌ Error crawling chat data for video_id {video_id}: {e}")
            return False


def _append_chats_to_jsonl(chats: list[tuple[int, str, int]], video_id: int):
    file_path = f"./data/chats/{video_id}.jsonl"
    try:
        # Append new chats as JSONL
        with open(file_path, "a", encoding="utf-8") as f:
            for chat in chats:
                chat_obj = {"timestamp": chat[0], "text": chat[1], "type_code": chat[2]}
                f.write(json.dumps(chat_obj, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error appending chats to jsonl file: {e}")
        raise e


def _parse_video_chats(data):
    content = data.get("content")
    if not content:
        logger.error(f"❌ No content found in data: {data}")
        raise ValueError(f"No content found in data: {data}")

    next_player_message_time = content.get("nextPlayerMessageTime")
    video_chats = content.get("videoChats")
    if not video_chats:
        logger.error(f"❌ No video chats found in data: {data}")
        raise ValueError(f"No video chats found in data: {data}")

    result = []

    for video_chat in video_chats:
        msg_type_code = video_chat.get("messageTypeCode")
        timestamp_ms = video_chat.get("playerMessageTime")
        text = video_chat.get("content")

        match msg_type_code:
            case 1:
                result.append((timestamp_ms, text, PROMPT_CMD_TO_TYPE_CODE["chat"]))
            case 10:
                result.append((timestamp_ms, text, PROMPT_CMD_TO_TYPE_CODE["donation"]))

    return result, next_player_message_time
