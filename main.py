import json
import threading
import time

from loguru import logger

from context.context_manager import ContextManager

with open("context/config.json") as f:
    context_config = json.load(f)


def periodic_task():
    while not stop_event.is_set():
        logger.info("[주기적 호출] context 분석")
        context_prompt = context_manager.get_context_prompt()
        print(context_prompt)
        time.sleep(2)  # 5초 간격


if __name__ == "__main__":
    stop_event = threading.Event()
    channel_id = ""  # channel_id

    context_manager = ContextManager(channel_id, context_config)

    # Start context manager in a separate thread
    context_thread = threading.Thread(target=context_manager.run)
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
        context_manager.stop()
        context_thread.join(timeout=5.0)
        periodic_thread.join(timeout=5.0)
        print(threading.active_count())  # 2, main and garbage collector(expected)
