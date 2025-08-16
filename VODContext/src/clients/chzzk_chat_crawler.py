import os
import random
import re
import time

import orjson
import requests
from loguru import logger

from config import Config
from schemas.context_data import ContextData


class ChzzkChatCrawler:
    def __init__(self, config: Config):
        self.chat_url = config.ChzzkChat.CHAT_URL
        self.user_agent = config.Network.USER_AGENT
        self.prompt_cmd_to_type_code = config.Service.PROMPT_CMD_TO_TYPE_CODE
        self.chat_context_dir = config.DataDir.CHAT_CONTEXT_DIR
        self.message_type_code_to_prompt_cmd = config.Service.CHZZK_MESSAGE_TYPE_CODE_TO_PROMPT_CMD
        self.max_retries = config.Network.HTTP_MAX_RETRIES
        self.base_sleep_time = config.Network.HTTP_BASE_SLEEP_TIME

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

    def _append_chats_to_jsonl(self, chat_contexts: list[ContextData], video_no: int):
        output_path = os.path.join(self.chat_context_dir, f"{video_no}.jsonl")
        try:
            # Append new chats as JSONL
            with open(output_path, "ab") as f:
                for context in chat_contexts:
                    f.write(orjson.dumps(context.model_dump()) + b"\n")
        except Exception as e:
            logger.error(f"Error appending chats to jsonl file: {e}")
            raise e

    def _preprocess_chat_message_to_prompt_str(self, chat_message: str) -> str:
        chat_message = re.sub(r"\{:[^:]*:\}", "", chat_message)
        chat_message = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1{2,}", r"\1\1", chat_message)

        return chat_message.strip()

    def _parse_video_chats(self, data) -> tuple[list[ContextData], int]:
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
                extras = orjson.loads(extras)
                pay_amount = extras.get("payAmount", 0)
            prompt_str = self._preprocess_chat_message_to_prompt_str(content)
            # chzzk 서비스에 적용하는 chat, donation의 msg_type_code -> 'chat', 'donation' -> 내 서비스에서 사용할 chat, donation의 코드드 매핑 적용
            type_code = self.prompt_cmd_to_type_code[self.message_type_code_to_prompt_cmd[msg_type_code]]

            context_data = ContextData(
                timestamp_ms=timestamp_ms,
                content=content,
                type_code=type_code,
                prompt_str=prompt_str,
                pay_amount=pay_amount,
            )
            result.append(context_data)

        return result, next_player_message_time

    def crawl_chat(self, video_no: int, additional_sleep_time: float = 0) -> bool:
        next_player_message_time = 0
        retry_count = 0
        sleep_time = self.base_sleep_time + additional_sleep_time

        while next_player_message_time is not None:
            try:
                data = self._request_chzzk_chats(video_no, next_player_message_time)
                if not data:
                    if retry_count < self.max_retries:
                        retry_count += 1
                        logger.warning(f"Retrying ({retry_count}/{self.max_retries}) for video_no: {video_no}")
                        continue
                    logger.error(
                        f"❌ Failed to crawl chat data for video_no: {video_no} after {self.max_retries} retries"
                    )
                    return False

                video_chats, next_player_message_time = self._parse_video_chats(data)
                logger.info(f"next_player_message_time :{next_player_message_time}")
                self._append_chats_to_jsonl(video_chats, video_no)
                retry_count = 0  # Reset retry count on success
                time.sleep(sleep_time * random.uniform(0.5, 1.5))
            except Exception as e:
                logger.error(f"❌ Error crawling chat data for video_no {video_no}: {e}")
                return False
        return True
