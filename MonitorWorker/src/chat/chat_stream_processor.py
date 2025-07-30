import datetime
import json
import re
import threading
import time
from collections import deque

from loguru import logger
from websocket import WebSocket

from chat import api
from data_types.context_data import ContextData


class ChatStreamProcessor:
    STOP_TIMEOUT_S = 5

    def __init__(self, streamer_id: str, chat_config, shared_config):
        self.streamer_id = streamer_id
        self.chzzk_chat_code = chat_config.CHZZK_CHAT_CODE
        self.sid = None
        self.chatChannelId = api.fetch_chatChannelId(streamer_id)
        self.channelName = api.fetch_channelName(streamer_id)
        self.accessToken, self.extraToken = None, None
        self.userIdHash = api.fetch_userIdHash()

        self.prompt_cmd_to_type_code = shared_config.PROMPT_CMD_TO_TYPE_CODE
        self.type_code_to_prompt_cmd = {v: k.upper() for k, v in self.prompt_cmd_to_type_code.items()}
        self.is_running = False
        self.stop_event = threading.Event()
        self.chat_thread = None
        self.chat_history: deque[ContextData] = deque(maxlen=chat_config.MAX_CHAT_HISTORY_COUNT)
        self.chat_history_lock = threading.Lock()

        self._connect()

    def _connect(self):
        if hasattr(self, "sock") and self.sock.connected:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")

        self.chatChannelId = api.fetch_chatChannelId(self.streamer_id)
        self.accessToken, self.extraToken = api.fetch_accessToken(self.chatChannelId)

        sock = WebSocket()
        sock.connect("wss://kr-ss1.chat.naver.com/chat")
        logger.info(f"{self.channelName} 채팅창에 연결 중 .")

        default_dict = {
            "ver": "2",
            "svcid": "game",
            "cid": self.chatChannelId,
        }

        send_dict = {
            "cmd": self.chzzk_chat_code["connect"],
            "tid": 1,
            "bdy": {
                "uid": self.userIdHash,
                "devType": 2001,
                "accTkn": self.accessToken,
                "auth": "READ",
            },
        }

        sock.send(json.dumps(dict(send_dict, **default_dict)))
        sock_response = json.loads(sock.recv())
        self.sid = sock_response["bdy"]["sid"]
        logger.info(f"\r{self.channelName} 채팅창에 연결 중 ..")

        send_dict = {
            "cmd": self.chzzk_chat_code["request_recent_chat"],
            "tid": 2,
            "sid": self.sid,
            "bdy": {"recentMessageCount": 50},
        }

        sock.send(json.dumps(dict(send_dict, **default_dict)))
        sock.recv()
        logger.info(f"\r{self.channelName} 채팅창에 연결 중 ...")

        self.sock = sock
        if self.sock.connected:
            logger.info("연결 완료")
        else:
            logger.error("오류 발생")
            raise ValueError("오류 발생")

    def send(self, message: str):
        default_dict = {
            "ver": 2,
            "svcid": "game",
            "cid": self.chatChannelId,
        }

        extras = {
            "chatType": "STREAMING",
            "emojis": "",
            "osType": "PC",
            "extraToken": self.extraToken,
            "streamingChannelId": self.chatChannelId,
        }

        send_dict = {
            "tid": 3,
            "cmd": self.chzzk_chat_code["send_chat"],
            "retry": False,
            "sid": self.sid,
            "bdy": {
                "msg": message,
                "msgTypeCode": 1,
                "extras": json.dumps(extras),
                "msgTime": int(datetime.datetime.now().timestamp()),
            },
        }

        self.sock.send(json.dumps(dict(send_dict, **default_dict)))

    def _preprocess_chat_message_to_prompt_str(self, chat_message: str) -> str:
        chat_message = re.sub(r"\{:[^:]*:\}", "", chat_message)
        chat_message = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1{2,}", r"\1\1", chat_message)

        return chat_message.strip()

    def _process_chat_message(self, raw_message):
        """채팅 메시지를 처리하고 큐에 추가"""
        try:
            chat_code = raw_message["cmd"]  # 한개가 아닌 경우가 있음

            if chat_code == self.chzzk_chat_code["ping"]:
                self.sock.send(json.dumps({"ver": "2", "cmd": self.chzzk_chat_code["pong"]}))

                if self.chatChannelId != api.fetch_chatChannelId(self.streamer_id):
                    self._connect()
                return

            if chat_code == self.chzzk_chat_code["chat"]:
                chat_type_code = self.prompt_cmd_to_type_code["chat"]
            elif chat_code == self.chzzk_chat_code["donation"]:
                chat_type_code = self.prompt_cmd_to_type_code["donation"]
            else:
                return

            for chat_data in raw_message["bdy"]:
                # timestamp_ms = int(datetime.datetime.now().timestamp() * 1000)
                timestamp_ms = int(
                    chat_data["msgTime"]
                )  # 내 데스크탑 환경에 따라 시간이 튐 맥에서 대여한 gpu에서는 정상
                processed_msg = self._preprocess_chat_message_to_prompt_str(chat_data["msg"])
                prompt_str = f"{processed_msg}\n" if processed_msg else ""

                chat_info = ContextData(timestamp_ms, chat_data["msg"], chat_type_code, prompt_str)

                # 채팅 히스토리에 추가
                with self.chat_history_lock:
                    self.chat_history.append(chat_info)

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")

    def _chat_worker(self):
        """채팅 메시지를 처리하는 워커 스레드"""
        while not self.stop_event.is_set():
            try:
                raw_message = self.sock.recv()
                raw_message = json.loads(raw_message)
                self._process_chat_message(raw_message)
            except Exception as e:
                logger.error(f"Error in chat worker: {e}")
                if not self.stop_event.is_set():
                    self._connect()

    def run(self):
        if self.is_running:
            return

        self.is_running = True
        self.stop_event.clear()

        self.chat_thread = threading.Thread(target=self._chat_worker)
        self.chat_thread.daemon = True
        self.chat_thread.start()

    def stop(self):
        if not self.is_running:
            return

        logger.info("\nStopping ChatProcessor...")
        self.is_running = False
        self.stop_event.set()

        if self.chat_thread and self.chat_thread.is_alive():
            self.chat_thread.join(timeout=self.STOP_TIMEOUT_S)
            logger.info("Chat worker thread stopped.")

    def get_new_chats(self) -> list[ContextData]:
        with self.chat_history_lock:
            latest_chats = list(self.chat_history)
            self.chat_history.clear()
        return latest_chats


if __name__ == "__main__":
    CHAT_CONFIG = {
        "max_chat_history_count": 10000,
        "chzzk_chat_code": {
            "ping": 0,
            "pong": 10000,
            "connect": 100,
            "send_chat": 3101,
            "request_recent_chat": 5101,
            "chat": 93101,
            "donation": 93102,
        },
    }

    SHARED_CONFIG = {"prompt_cmd_to_type_code": {"chat": 100, "donation": 1000, "asr": 10000}}

    channel_id = ""

    chat_stream_processor = ChatStreamProcessor(channel_id, CHAT_CONFIG, SHARED_CONFIG)
    chat_stream_processor.run()

    while True:
        time.sleep(1)
        new_chats = chat_stream_processor.get_new_chats()
        for chat in new_chats:
            logger.info(chat)
