import itertools
from datetime import date, datetime

from loguru import logger
from sqlalchemy.inspection import inspect

# --- 의존성 임포트 ---
# Celery 관련 (미래를 위해 주석 처리)
# from ..celery_app import celery_app
# 우리가 만든 모듈들
from chatzzk.packages.data_access import database
from chatzzk.packages.schemas.db_models import ChzzkVodORM
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)

chzzk_client = ChzzkPlatformClient()


def _parse_date_string(date_str: str | None, video_no: str) -> datetime | None:
    """날짜 문자열을 datetime 객체로 파싱하는 헬퍼 함수."""
    if not date_str:
        return None
    try:
        # API 응답 형식에 맞춰 파싱 (예: "2024-08-29 14:30:00")
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        logger.warning(f"Invalid date format for VOD {video_no}: '{date_str}'.")
        return None


# --- 이 파일이 책임지는 작업(Job) ---
# @celery_app.task(name="jobs.fetch_new_chzzk_vods")
def fetch_new_vods_for_channel(channel_id: str, limit: int | None = None, stop_before_date: date | None = None):
    """
    특정 채널의 VOD 목록을 가져와 DB에 없는 새로운 VOD 정보만 저장합니다.

    Args:
        channel_id (str): 대상 채널의 ID.
        limit (Optional[int]): 가져올 최대 VOD 개수. None이면 제한 없음.
        stop_before_date (Optional[date]): 이 날짜 이전의 VOD는 수집을 중단합니다.
    """
    logger.info(
        f"🚀 Starting job: Fetch new VODs for channel '{channel_id}' (limit={limit}, stop_before_date={stop_before_date})"
    )

    try:
        # 1. 플랫폼에서 해당 채널의 모든 VOD 번호 스트리밍
        video_nos_stream = chzzk_client.stream_all_video_numbers(channel_id)
        limited_stream = itertools.islice(video_nos_stream, limit)

        new_vod_count = 0
        processed_count = 0

        for video_no in limited_stream:
            processed_count += 1
            with database.get_db_session() as db:
                # 2. 우리 DB에 이미 존재하는 VOD인지 확인
                if database.get_vod_by_video_no(db, video_no):
                    logger.trace(f"VOD {video_no} already exists. Skipping.")
                    continue

            # 3. DB에 없다면, 플랫폼에 VOD 상세 정보 요청
            logger.info(f"Found new VOD: {video_no}. Fetching details...")
            details = chzzk_client.fetch_vod_details(video_no)
            if not details:
                logger.warning(f"Could not fetch details for new VOD {video_no}. Skipping.")
                continue

            vod_pydantic, _, _ = details

            # 1. 날짜 변환 (이 함수의 책임)
            publish_datetime = _parse_date_string(vod_pydantic.publish_date, video_no)

            # 2. 날짜 필터링
            if stop_before_date and publish_datetime:
                if publish_datetime.date() < stop_before_date:
                    logger.info(f"Reached stop_before_date ({stop_before_date}). Halting collection.")
                    break

            # 3. DB 저장을 위한 데이터 준비
            #    - ORM 모델에 있는 필드만 선택
            #    - 날짜 필드는 변환된 datetime 객체로 교체
            orm_columns = {c.key for c in inspect(ChzzkVodORM).column_attrs}
            vod_data_to_save = vod_pydantic.model_dump(include=orm_columns, by_alias=False)

            live_open_datetime = _parse_date_string(vod_pydantic.live_open_date, video_no)
            vod_data_to_save["publish_date"] = publish_datetime
            vod_data_to_save["live_open_date"] = live_open_datetime

            with database.get_db_session() as db:
                if database.create_vod_and_status(db, vod_data_to_save):
                    new_vod_count += 1
                    logger.success(f"✅ Successfully saved new VOD to DB: {vod_pydantic.video_title}")
                else:
                    logger.error(f"❌ Failed to save new VOD {video_no} to DB.")

        logger.info(
            f"✨ Job finished for channel '{channel_id}'. Processed: {processed_count}, New VODs added: {new_vod_count}."
        )

    except Exception as e:
        logger.opt(exception=True).error(
            f"An unexpected error occurred during 'fetch_new_vods' job for channel {channel_id}: {e}"
        )
        # 실패 시 에러를 다시 발생시켜 Celery 등이 실패를 인지하게 함
        raise


if __name__ == "__main__":
    CHANNEL_ID = "b044e3a3b9259246bc92e863e7d3f3b8"
    fetch_new_vods_for_channel(CHANNEL_ID, 10)
