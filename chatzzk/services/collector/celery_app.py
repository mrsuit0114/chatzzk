from celery import Celery

from chatzzk.services.collector.settings import collector_settings

celery_collector_app = Celery(
    "collector",  # 이 서비스의 Celery 앱 이름
    broker=collector_settings.celery_broker_url,
    backend=collector_settings.celery_result_backend,
    # Celery가 자동으로 Task를 찾을 경로
    include=[
        "chatzzk.services.collector.jobs.tasks.discovery",
        "chatzzk.services.collector.jobs.tasks.processing",
    ],
)

celery_collector_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)
