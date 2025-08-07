import json
import os
import random
import re
import time

import requests
from loguru import logger

from config import ChzzkChatCrawlerConfig
from data_types.context_data import ContextData


class ChzzkChatCrawler:
    MAX_RETRIES = 3

    def __init__(self, config: ChzzkChatCrawlerConfig):
        self.chat_url = config.CHAT_URL
        self.user_agent = config.USER_AGENT
        self.prompt_cmd_to_type_code = config.PROMPT_CMD_TO_TYPE_CODE
        self.data_dir = config.DATA_DIR
        self.chat_context_dir = config.CHAT_CONTEXT_DIR
        self.message_type_code_to_prompt_cmd = config.MESSAGE_TYPE_CODE_TO_PROMPT_CMD

    def _request_chzzk_chats(self, video_no: int, player_message_time: int):
        url = self.chat_url.format(video_no=video_no)
        params = {"playerMessageTime": player_message_time}
        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            return None

    def _append_chats_to_jsonl(self, chats: list[ContextData], video_no: int):
        output_path = os.path.join(self.data_dir, self.chat_context_dir, f"{video_no}.jsonl")
        try:
            # Append new chats as JSONL
            with open(output_path, "a", encoding="utf-8") as f:
                for chat in chats:
                    chat_obj = {
                        "timestamp_ms": chat.timestamp_ms,
                        "content": chat.content,
                        "type_code": chat.type_code,
                        "prompt_str": chat.prompt_str,
                        "pay_amount": chat.pay_amount,
                    }
                    f.write(json.dumps(chat_obj, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error appending chats to jsonl file: {e}")
            raise e

    def _preprocess_chat_message_to_prompt_str(self, chat_message: str) -> str:
        chat_message = re.sub(r"\{:[^:]*:\}", "", chat_message)
        chat_message = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1{2,}", r"\1\1", chat_message)

        return chat_message.strip()

    def _parse_video_chats(self, data):
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
            if msg_type_code not in self.message_type_code_to_prompt_cmd:
                continue

            timestamp_ms = video_chat.get("playerMessageTime")
            content = video_chat.get("content")
            extras = video_chat.get("extras", None)
            pay_amount = 0
            if extras:
                extras = json.loads(extras)
                pay_amount = extras.get("payAmount", 0)
            prompt_str = self._preprocess_chat_message_to_prompt_str(content)
            type_code = self.prompt_cmd_to_type_code[self.message_type_code_to_prompt_cmd[msg_type_code]]

            context_data = ContextData(timestamp_ms, content, type_code, prompt_str, pay_amount)
            result.append(context_data)

        return result, next_player_message_time

    def crawl_chat(self, video_no: int, base_sleep_time: float = 0.5):
        next_player_message_time = 0
        retry_count = 0

        while next_player_message_time is not None:
            try:
                data = self._request_chzzk_chats(video_no, next_player_message_time)
                if not data:
                    if retry_count < self.MAX_RETRIES:
                        retry_count += 1
                        logger.warning(f"Retrying ({retry_count}/{self.MAX_RETRIES}) for video_no: {video_no}")
                        continue
                    logger.error(
                        f"❌ Failed to crawl chat data for video_no: {video_no} after {self.MAX_RETRIES} retries"
                    )
                    return False

                video_chats, next_player_message_time = self._parse_video_chats(data)
                print("next_player_message_time", next_player_message_time)
                self._append_chats_to_jsonl(video_chats, video_no)
                retry_count = 0  # Reset retry count on success
                time.sleep(base_sleep_time * random.uniform(0.5, 1.5))
            except Exception as e:
                logger.error(f"❌ Error crawling chat data for video_no {video_no}: {e}")
                return False
