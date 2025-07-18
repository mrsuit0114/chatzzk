# import json
# import os
# import threading
# import time

# from context_manager import ContextManager
# from loguru import logger

# with open("config.json") as f:
#     context_config = json.load(f)


# def periodic_task():
#     while not stop_event.is_set():
#         logger.info("[주기적 호출] context 분석")
#         context_prompt = context_manager.get_context_prompt()
#         print(context_prompt)
#         time.sleep(2)  # 5초 간격


# if __name__ == "__main__":
#     stop_event = threading.Event()
#     channel_id = os.environ.get("CHANNEL_ID", "")  # channel_id

#     context_manager = ContextManager(channel_id, context_config)

#     # Start context manager in a separate thread
#     context_thread = threading.Thread(target=context_manager.run)
#     context_thread.start()

#     # Start periodic task in a separate thread
#     periodic_thread = threading.Thread(target=periodic_task)
#     periodic_thread.start()

#     try:
#         # Keep main thread alive
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n프로그램 종료 중...")
#         stop_event.set()
#         context_manager.stop()
#         context_thread.join(timeout=5.0)
#         periodic_thread.join(timeout=5.0)
#         print(threading.active_count())  # 2, main and garbage collector(expected)

import time

from chat.chat_stream_processor import ChatStreamProcessor
from loguru import logger

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
