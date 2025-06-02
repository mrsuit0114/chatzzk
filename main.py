import json
import threading
import time

from context.context_manager import ContextManager

with open("config/config.json") as f:
    config = json.load(f)


def ms_to_time(ms: int) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(ms / 1000))


def periodic_task():
    while not stop_event.is_set():
        print("[주기적 호출] context 분석")
        context_audio = context_manager.get_context()
        for context in context_audio:
            print(f"{ms_to_time(context.timestamp_ms)} [{context.type}] {context.content}")
        time.sleep(2)  # 5초 간격


if __name__ == "__main__":
    stop_event = threading.Event()
    channel_id = ""  # channel_id

    context_manager = ContextManager(channel_id, config)

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
