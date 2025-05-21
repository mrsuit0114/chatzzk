import argparse
import datetime
import json
import logging

from websocket import WebSocket

import api
from cmd_type import CHZZK_CHAT_CMD


class ChzzkChat:
    def __init__(self, streamer, logger):
        self.streamer = streamer
        self.logger = logger

        self.sid = None
        self.chatChannelId = api.fetch_chatChannelId(self.streamer)
        self.channelName = api.fetch_channelName(self.streamer)
        self.accessToken, self.extraToken = None, None
        self.userIdHash = api.fetch_userIdHash()

        self.connect()

    def connect(self):
        self.chatChannelId = api.fetch_chatChannelId(self.streamer)
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
            "cmd": CHZZK_CHAT_CMD["connect"],
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
            "cmd": CHZZK_CHAT_CMD["request_recent_chat"],
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
            "cmd": CHZZK_CHAT_CMD["send_chat"],
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

    def run(self):
        while True:
            try:
                try:
                    raw_message = self.sock.recv()

                except KeyboardInterrupt:
                    break

                except Exception:
                    self.connect()
                    raw_message = self.sock.recv()

                raw_message = json.loads(raw_message)
                chat_cmd = raw_message["cmd"]  # 한개가 아닌 경우가 있긴 함

                if chat_cmd == CHZZK_CHAT_CMD["ping"]:
                    self.sock.send(json.dumps({"ver": "2", "cmd": CHZZK_CHAT_CMD["pong"]}))

                    if self.chatChannelId != api.fetch_chatChannelId(
                        self.streamer
                    ):  # 방송 시작시 chatChannelId가 달라지는 문제
                        self.connect()

                    continue

                if chat_cmd == CHZZK_CHAT_CMD["chat"]:
                    chat_type = "CHAT"

                elif chat_cmd == CHZZK_CHAT_CMD["donation"]:
                    chat_type = "DONATION"

                else:
                    continue

                for chat_data in raw_message["bdy"]:
                    now = datetime.datetime.fromtimestamp(chat_data["msgTime"] / 1000)
                    now = datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S")

                    self.logger.info(f"[{now}][{chat_type}] {chat_data['msg']}")

            except Exception:
                pass


def get_logger():
    formatter = logging.Formatter("%(message)s")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("chat.log", mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--streamer_id", type=str, default="e9c11510c1c6097a20b92ebcb289b26a")
    args = parser.parse_args()

    logger = get_logger()
    chzzkchat = ChzzkChat(args.streamer_id, logger)

    # 채팅창으로 메세지 보내기
    # mesaage = ' '
    # chzzkchat.send(message=mesaage)

    # 채팅 크롤링
    chzzkchat.run()
