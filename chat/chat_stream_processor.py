import bisect
import datetime
import json
import threading
from collections import deque

from loguru import logger
from websocket import WebSocket

import chat.api as api
from data_types.context_data import ContextData


class ChatStreamProcessor:
    def __init__(self, streamer_id: str, chat_config: dict):
        self.streamer_id = streamer_id
        self.context_duration_ms = chat_config["chat_context_duration_ms"]
        self.chat_cmd = chat_config["chzzk_chat_cmd"]

        self.sid = None
        self.chatChannelId = api.fetch_chatChannelId(self.streamer_id)
        self.channelName = api.fetch_channelName(self.streamer_id)
        self.accessToken, self.extraToken = None, None
        self.userIdHash = api.fetch_userIdHash()

        # 채팅 메시지를 저장할 큐와 스레드 관련 변수들
        self.is_running = False
        self.stop_event = threading.Event()
        self.chat_thread = None
        self.chat_history = deque(maxlen=chat_config["max_chat_history_count"])
        self.chat_history_lock = threading.Lock()

        self.connect()

    def connect(self):
        self.chatChannelId = api.fetch_chatChannelId(self.streamer_id)
        self.accessToken, self.extraToken = api.fetch_accessToken(self.chatChannelId)

        sock = WebSocket()
        sock.connect("wss://kr-ss1.chat.naver.com/chat")
        print(f"{self.channelName} 채팅창에 연결 중 .", end="")

        default_dict = {
            "ver": "2",
            "svcid": "game",
            "cid": self.chatChannelId,
        }

        send_dict = {
            "cmd": self.chat_cmd["connect"],
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
        print(f"\r{self.channelName} 채팅창에 연결 중 ..", end="")

        send_dict = {
            "cmd": self.chat_cmd["request_recent_chat"],
            "tid": 2,
            "sid": self.sid,
            "bdy": {"recentMessageCount": 50},
        }

        sock.send(json.dumps(dict(send_dict, **default_dict)))
        sock.recv()
        print(f"\r{self.channelName} 채팅창에 연결 중 ...")

        self.sock = sock
        if self.sock.connected:
            print("연결 완료")
        else:
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
            "cmd": self.chat_cmd["send_chat"],
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

    def _process_chat_message(self, raw_message):
        """채팅 메시지를 처리하고 큐에 추가"""
        try:
            chat_cmd = raw_message["cmd"]  # 한개가 아닌 경우가 있음

            if chat_cmd == self.chat_cmd["ping"]:
                self.sock.send(json.dumps({"ver": "2", "cmd": self.chat_cmd["pong"]}))

                if self.chatChannelId != api.fetch_chatChannelId(self.streamer_id):
                    self.connect()
                return

            if chat_cmd == self.chat_cmd["chat"]:
                chat_type = "CHAT"
            elif chat_cmd == self.chat_cmd["donation"]:
                chat_type = "DONATION"
            else:
                return

            for chat_data in raw_message["bdy"]:
                timestamp_ms = chat_data["msgTime"]  # 이미 밀리초 단위로 제공됨

                chat_info = ContextData(timestamp_ms, chat_data["msg"], chat_type)

                # 채팅 히스토리에 추가
                with self.chat_history_lock:
                    self.chat_history.append(chat_info)

                # 로깅 (필요한 경우에만 문자열로 변환)
                # now = datetime.datetime.fromtimestamp(timestamp_ms / 1000)
                # now = datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
                # self.logger.info(f"[{now}][{chat_type}] {chat_data['msg']}")

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
                    self.connect()

    def run(self):
        """비동기로 채팅 수집 시작"""
        if self.is_running:
            return

        self.is_running = True
        self.stop_event.clear()

        # 채팅 워커 스레드 시작
        self.chat_thread = threading.Thread(target=self._chat_worker)
        self.chat_thread.daemon = True
        self.chat_thread.start()

        # 메인 스레드는 종료 신호를 기다리면서 대기
        try:
            while not self.stop_event.is_set():
                self.stop_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Stopping chat collection...")
        finally:
            self.stop()

    def stop(self):
        """채팅 수집 중지"""
        if not self.is_running:
            return

        print("\nStopping ChatProcessor...")
        self.is_running = False
        self.stop_event.set()

        # 채팅 스레드 종료 대기
        if self.chat_thread and self.chat_thread.is_alive():
            self.chat_thread.join(timeout=5.0)
            print("Chat worker thread stopped.")

    def get_latest_chats_since(self, timestamp_ms: int) -> list:
        threshold_ms = timestamp_ms - self.context_duration_ms
        with self.chat_history_lock:
            idx = bisect.bisect_left(self.chat_history, threshold_ms, key=lambda x: x.timestamp_ms)
            return list(self.chat_history)[idx:]
