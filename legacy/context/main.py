import os
import threading
import time

from config import ContextFetcherConfig
from context_fetcher import ContextFetcher
from loguru import logger


def periodic_task():
    while not stop_event.is_set():
        logger.info("[주기적 호출] context 분석")
        context_prompt = context_fetcher.get_context_prompt()
        logger.info(f"\n{context_prompt}")
        time.sleep(2)  # 5초 간격


if __name__ == "__main__":
    stop_event = threading.Event()
    channel_id = os.environ.get("CHANNEL_ID", "")  # channel_id

    context_fetcher = ContextFetcher(channel_id, ContextFetcherConfig)

    # Start context manager in a separate thread
    context_thread = threading.Thread(target=context_fetcher.run)
    context_thread.start()

    # Start periodic task in a separate thread
    periodic_thread = threading.Thread(target=periodic_task)
    periodic_thread.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n프로그램 종료 중...")
        stop_event.set()
        context_fetcher.stop()
        context_thread.join(timeout=5.0)
        periodic_thread.join(timeout=5.0)
        print(threading.active_count())  # 2, main and garbage collector(expected)

# import os
# import time

# from chat.chat_stream_processor import ChatStreamProcessor
# from config import ChatConfig, SharedConfig
# from loguru import logger

# channel_id = os.environ.get("CHANNEL_ID", "")

# chat_stream_processor = ChatStreamProcessor(channel_id, ChatConfig, SharedConfig)
# chat_stream_processor.run()

# while True:
#     time.sleep(1)
#     new_chats = chat_stream_processor.get_new_chats()
#     for chat in new_chats:
#         logger.info(chat)
