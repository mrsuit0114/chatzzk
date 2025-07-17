import os


class Config:
    # redis서버 url
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    # watcher에서 보내는 stream을 받을 stream_key
    CHZZK_LIVE_STATUS_STREAM = "chzzk_live_status_events"
    # manger간 상호 배타적인 데이터 처리를 위한 group_name
    MONITOR_MANAGER_GROUP = "monitor_managers_group"
    # consumername
    MONITOR_MANAGER_ID = "monitor_manager-default"

    MONITORING_POD_IMAGE = "monitor_worker"
    KUBERNETES_NAMESPACE = "default"
    MONITORING_GRACE_PERIOD_SECONDS = 30
