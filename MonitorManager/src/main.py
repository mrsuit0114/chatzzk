# main.py
from loguru import logger

from config import Config
from kubernetes_client import KubernetesClient
from monitor_manager import MonitorManager
from redis_client import RedisClient
from stream_consumer import StreamConsumer


def main():
    logger.info(f"Starting Monitor Manager with ID: {Config.MONITOR_MANAGER_ID}")

    # 환경 변수 유효성 검사 (선택 사항)
    if not Config.MONITORING_POD_IMAGE:
        logger.error("Error: MONITORING_POD_IMAGE environment variable is not set.")
        exit(1)

    # 클라이언트 초기화
    redis_client = RedisClient(Config.REDIS_URL)
    k8s_client = KubernetesClient()

    # 매니저 초기화
    monitor_manager = MonitorManager(k8s_client, redis_client)
    stream_consumer = StreamConsumer(redis_client, monitor_manager)

    # Redis Stream 메시지 소비 시작
    logger.info("run start")
    stream_consumer.run()


if __name__ == "__main__":
    main()
