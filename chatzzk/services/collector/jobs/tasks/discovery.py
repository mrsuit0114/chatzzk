from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.inspection import inspect

from chatzzk.packages.data_access import database
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.schemas.db_models import ChzzkVodORM
from chatzzk.services.collector.celery_app import celery_collector_app
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient

chzzk_client = ChzzkPlatformClient()


def _parse_date_string(date_str: str | None) -> datetime | None:
    """날짜 문자열을 timezone-aware한 UTC datetime 객체로 파싱합니다."""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        if date_str.tzinfo is None:
            return date_str.replace(tzinfo=UTC)
        return date_str
    try:
        naive_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        # 생성된 naive datetime에 UTC 시간대 정보를 부여하여 aware datetime으로 변환
        return naive_dt.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        raise


@celery_collector_app.task(name="collector.discover_new_vods", bind=True, max_retries=3, default_retry_delay=300)
def discover_new_vods_for_channel(self, channel_id: str):
    """
    [Celery Task] 특정 채널의 새로운 VOD를 탐색하여 DB에 'PENDING' 상태로 등록합니다.
    """
    logger.info(f"🚀 [Task ID: {self.request.id}] Starting VOD discovery for channel_id: {channel_id}")

    try:
        # 작업 시작 전 초기 정보 조회 (첫 번째 세션)
        with database.get_db_session() as db:
            channel_repo = ChannelRepository(db)
            channel = channel_repo.get_by_channel_id(channel_id)
            if not channel:
                logger.error(f"Channel with id '{channel_id}' not found in DB. Aborting task.")
                return f"Non-retryable error: Channel {channel_id} not found."
            last_crawled_at = channel.last_vod_crawled_at
            channel_name = channel.channel_name

        logger.info(f"Processing channel '{channel_name}'. Last crawled at: {last_crawled_at}.")
        cur_last_crawled_at = datetime.now(UTC)
        video_nos_stream = chzzk_client.stream_all_video_numbers(channel_id)

        new_vod_count = 0
        processed_count = 0

        for video_no in video_nos_stream:
            # VOD 존재 여부 확인 (루프 내 별도 세션)
            with database.get_db_session() as db:
                vod_repo = VodRepository(db)
                if vod_repo.get_by_video_no(video_no):
                    logger.trace(f"VOD {video_no} already exists in DB. Skipping.")
                    continue

            # --- DB 세션이 없는 구간 (외부 API 호출 등) ---
            processed_count += 1
            details = chzzk_client.fetch_vod_details(video_no)
            if not details:
                logger.warning(f"Could not fetch details for VOD {video_no}. Skipping.")
                continue

            vod_pydantic, _, _ = details
            publish_datetime = _parse_date_string(vod_pydantic.publish_date)
            if last_crawled_at and publish_datetime and publish_datetime <= last_crawled_at:
                logger.info(
                    f"VOD {video_no} ({publish_datetime}) is older than or same as last crawl time. Halting collection for this channel."
                )
                break
            # --- DB 세션이 없는 구간 끝 ---

            # VOD 생성을 위한 데이터 준비
            orm_columns = {c.key for c in inspect(ChzzkVodORM).column_attrs}
            vod_data_to_save = vod_pydantic.model_dump(include=orm_columns)
            vod_data_to_save["publish_date"] = publish_datetime
            vod_data_to_save["live_open_date"] = _parse_date_string(vod_pydantic.live_open_date)

            # VOD 생성 (루프 내 별도 세션)
            with database.get_db_session() as db:
                channel_repo = ChannelRepository(db)
                channel_in_session = channel_repo.get_by_channel_id(channel_id)

                vod_repo = VodRepository(db)
                if vod_repo.create(channel_in_session, vod_data_to_save):
                    new_vod_count += 1

        # 모든 VOD 탐색 성공 후, 채널의 마지막 스캔 시간 업데이트 (마지막 세션)
        with database.get_db_session() as db:
            channel_repo = ChannelRepository(db)
            channel_repo.update_last_crawled_at(channel_id, cur_last_crawled_at)

        result_message = (
            f"Completed for {channel_id}. Processed {processed_count} VODs, Added {new_vod_count} new VODs."
        )
        logger.info(f"✨ [Task ID: {self.request.id}] {result_message}")
        return result_message

    except Exception as e:
        logger.opt(exception=True).error(
            f"❌ [Task ID: {self.request.id}] An unexpected error occurred during VOD discovery for {channel_id}. Retrying..."
        )
        raise self.retry(exc=e) from e
