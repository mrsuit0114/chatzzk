from dependency_injector.wiring import Provide, inject
from loguru import logger

from chatzzk.services.collector.celery_app import celery_collector_app
from chatzzk.services.collector.container import Container
from chatzzk.services.collector.services.vod_processing_service import (
    VodProcessingService,
)


@celery_collector_app.task(name="collector.process_vod_to_context", bind=True, max_retries=2, default_retry_delay=600)
@inject
def process_vod_to_context(
    self,
    vod_pk: int,
    service: VodProcessingService = Provide[Container.vod_processing_service],
):
    """
    [Celery Task] VOD 처리 파이프라인을 시작합니다.
    핵심 로직은 VodProcessingService에 위임합니다.
    """
    logger.info(f"🚀 [Task ID: {self.request.id}] Received VOD processing task for vod_pk: {vod_pk}")
    try:
        # 서비스 호출! Task는 이제 '어떻게' 처리하는지 알 필요가 없습니다.
        result_message = service.process(vod_pk=vod_pk)

        logger.info(f"✨ [Task ID: {self.request.id}] {result_message}")
        return result_message

    except ValueError as e:
        # 서비스에서 발생시킨 재시도가 의미 없는 에러 처리 (e.g., VOD ID를 찾을 수 없음)
        logger.error(f"Non-retryable error for vod_pk {vod_pk}: {e}")
        return str(e)  # Celery 재시도를 트리거하지 않고 정상 종료

    except Exception as e:
        logger.opt(exception=True).error(
            f"❌ [Task ID: {self.request.id}] An unexpected error occurred for vod_pk {vod_pk}. Retrying..."
        )
        raise self.retry(exc=e) from e
