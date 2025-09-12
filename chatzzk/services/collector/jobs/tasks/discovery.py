from collections import namedtuple
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.inspection import inspect

from chatzzk.packages.data_access import database
from chatzzk.packages.schemas.db_models import ChzzkChannelORM, ChzzkVodORM
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient

chzzk_client = ChzzkPlatformClient()


# Define a simple mock object for the self argument
MockRequest = namedtuple("MockRequest", ["id"])
MockSelf = namedtuple("MockSelf", ["request", "retry"])


# A simple retry function to mimic Celery's behavior
def mock_retry(exc):
    print(f"Mocking retry for exception: {exc}")
    raise exc


# Create the mock self object
mock_self_obj = MockSelf(request=MockRequest(id="test-task-id-12345"), retry=mock_retry)


def _parse_date_string(date_str: str | None, video_no: str) -> datetime | None:
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
        logger.warning(f"Invalid date format for VOD {video_no}: '{date_str}'.")
        return None


# @celery_collector_app.task(name="collector.discover_new_vods", bind=True, max_retries=3, default_retry_delay=300)
def discover_new_vods_for_channel(self, channel_id: str):
    """
    [Celery Task] 특정 채널의 새로운 VOD를 탐색하여 DB에 'PENDING' 상태로 등록합니다.
    """
    logger.info(f"🚀 [Task ID: {self.request.id}] Starting VOD discovery for channel_id: {channel_id}")

    try:
        with database.get_db_session() as db:
            channel = db.query(ChzzkChannelORM).filter(ChzzkChannelORM.channel_id == channel_id).first()
            if not channel:
                logger.error(f"Channel with id '{channel_id}' not found in DB. Aborting task.")
                # 재시도해도 소용없으므로, 에러를 발생시키지 않고 정상 종료
                return f"Non-retryable error: Channel {channel_id} not found."

            # DB 세션에서 분리된 객체로 만들기 위해 주요 정보만 추출
            channel_pk = channel.id
            last_crawled_at = channel.last_vod_crawled_at
            channel_name = channel.channel_name

        logger.info(f"Processing channel '{channel_name}'. Last crawled at: {last_crawled_at}.")

        # 플랫폼에서 VOD 번호 스트림 가져오기
        video_nos_stream = chzzk_client.stream_all_video_numbers(channel_id)

        new_vod_count = 0
        processed_count = 0

        for video_no in video_nos_stream:
            with database.get_db_session() as db:
                if database.get_vod_by_video_no(db, video_no):
                    logger.trace(f"VOD {video_no} already exists in DB. Skipping.")
                    continue

            processed_count += 1

            # VOD 상세 정보 가져오기
            details = chzzk_client.fetch_vod_details(video_no)
            if not details:
                logger.warning(f"Could not fetch details for VOD {video_no}. Skipping.")
                continue

            vod_pydantic, _, _ = details

            # 날짜 필터링 로직
            publish_datetime = _parse_date_string(vod_pydantic.publish_date, video_no)
            if last_crawled_at and publish_datetime and publish_datetime <= last_crawled_at:
                logger.info(
                    f"VOD {video_no} ({publish_datetime}) is older than or same as last crawl time. Halting collection for this channel."
                )
                break

            # DB 저장을 위한 데이터 준비
            orm_columns = {c.key for c in inspect(ChzzkVodORM).column_attrs}
            vod_data_to_save = vod_pydantic.model_dump(include=orm_columns)

            # 파싱된 datetime 객체로 교체
            vod_data_to_save["publish_date"] = publish_datetime
            vod_data_to_save["live_open_date"] = _parse_date_string(vod_pydantic.live_open_date, video_no)

            # DB에 VOD 생성
            with database.get_db_session() as db:
                # 작업에 사용할 채널 객체를 현재 세션에서 다시 로드
                channel_in_session = db.get(ChzzkChannelORM, channel_pk)
                if database.create_vod(db, channel_in_session, vod_data_to_save):
                    new_vod_count += 1

        # 모든 VOD 탐색 성공 후, 채널의 마지막 스캔 시간 업데이트
        with database.get_db_session() as db:
            channel_to_update = db.get(ChzzkChannelORM, channel_pk)
            # utcnow() 대신 timezone.utc를 인자로 주는 now() 사용
            channel_to_update.last_vod_crawled_at = datetime.now(UTC)
            db.commit()
            logger.success(f"Updated last_vod_crawled_at for channel {channel_id}.")

        result_message = (
            f"Completed for {channel_id}. Processed {processed_count} VODs, Added {new_vod_count} new VODs."
        )
        logger.info(f"✨ [Task ID: {self.request.id}] {result_message}")
        return result_message

    except Exception as e:
        # 네트워크 오류 등 일시적인 문제일 수 있으므로 재시도
        logger.opt(exception=True).error(
            f"❌ [Task ID: {self.request.id}] An unexpected error occurred during VOD discovery for {channel_id}. Retrying..."
        )
        raise self.retry(exc=e) from e


if __name__ == "__main__":
    test_channel_id = "4515b179f86b67b4981e16190817c580"
    discover_new_vods_for_channel(mock_self_obj, test_channel_id)
