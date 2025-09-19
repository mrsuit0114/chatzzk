from dependency_injector.wiring import Provide, inject
from loguru import logger

from chatzzk.services.collector.celery_app import celery_collector_app
from chatzzk.services.collector.container import Container  # 공유 인스턴스 import
from chatzzk.services.collector.services.vod_discovery_service import VodDiscoveryService


@celery_collector_app.task(name="collector.discover_new_vods", bind=True, max_retries=3, default_retry_delay=300)
@inject
def discover_new_vods_for_channel(
    self,
    channel_id: str,
    service: VodDiscoveryService = Provide[Container.vod_discovery_service],
):
    """
    [Celery Task] 특정 채널의 새로운 VOD를 탐색하여 DB에 'PENDING' 상태로 등록합니다.
    """
    logger.info(f"🚀 [Task ID: {self.request.id}] Starting VOD discovery for channel_id: {channel_id}")
    try:
        # Task는 더 이상 비즈니스 로직의 세부 사항을 알지 못합니다.
        # 서비스의 메서드를 호출하기만 하면 됩니다.
        processed_count, new_vod_count = service.discover_and_save_new_vods(channel_id=channel_id)

        result_message = (
            f"Completed for {channel_id}. Processed {processed_count} VODs, Added {new_vod_count} new VODs."
        )
        logger.info(f"✨ [Task ID: {self.request.id}] {result_message}")
        return result_message

    except ValueError as e:
        # 서비스에서 채널을 찾지 못하는 등, 재시도해도 소용없는 예외를 처리합니다.
        logger.error(f"Non-retryable error for channel {channel_id}: {e}")
        return str(e)  # Celery 재시도를 트리거하지 않고 정상 종료

    except Exception as e:
        logger.opt(exception=True).error(
            f"❌ [Task ID: {self.request.id}] An unexpected error occurred during VOD discovery for {channel_id}. Retrying..."
        )
        raise self.retry(exc=e) from e
