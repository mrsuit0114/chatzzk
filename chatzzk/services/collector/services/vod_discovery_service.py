from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.orm import Session

from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.schemas.data_models import ChzzkVodInfo
from chatzzk.packages.schemas.db_models import ChzzkVodORM
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import ChzzkPlatformClient


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
        return naive_dt.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date string: {date_str}")
        return None


class VodDiscoveryService:
    """VOD 탐색과 관련된 비즈니스 로직을 캡슐화합니다."""

    def __init__(
        self,
        db_session_provider: callable,  # DB 세션이 아닌 '세션 제공자'를 주입받습니다.
        chzzk_client: ChzzkPlatformClient,
    ):
        self.db_session_provider = db_session_provider
        self.chzzk_client = chzzk_client

    def discover_and_save_new_vods(self, channel_id: str) -> tuple[int, int]:
        """
        주어진 채널 ID에 대해 새로운 VOD를 탐색하고 DB에 저장합니다.
        오래 걸리는 API 호출 중에는 DB 세션을 열어두지 않습니다.
        :return: (처리된 VOD 수, 새로 추가된 VOD 수)
        """
        # --- 첫 번째 DB 작업: 채널 정보 조회 ---
        with self.db_session_provider() as db:
            channel_repo = ChannelRepository(db)
            channel = channel_repo.get_by_channel_id(channel_id)
            if not channel:
                # 이 예외는 Task 레벨에서 non-retryable로 처리될 수 있습니다.
                raise ValueError(f"Channel with id '{channel_id}' not found in DB.")
            last_crawled_at = channel.last_vod_crawled_at
            logger.info(f"Processing channel '{channel.channel_name}'. Last crawled at: {last_crawled_at}.")
        # <-- 첫 번째 DB 세션은 여기서 안전하게 닫힙니다.

        # --- DB 세션이 없는 구간: 오래 걸릴 수 있는 외부 API 호출 ---
        video_nos_stream = self.chzzk_client.stream_all_video_numbers(channel_id)

        new_vod_count = 0
        processed_count = 0

        for video_no in video_nos_stream:
            processed_count += 1

            # --- 루프 내 DB 작업: VOD 존재 여부 확인 ---
            with self.db_session_provider() as db:
                vod_repo = VodRepository(db)
                if vod_repo.get_by_video_no(video_no):
                    logger.trace(f"VOD {video_no} already exists in DB. Skipping.")
                    continue
            # <-- VOD 확인용 세션은 여기서 즉시 닫힙니다.

            # --- DB 세션이 없는 구간: 상세 정보 API 호출 ---
            details = self.chzzk_client.fetch_vod_details(video_no)
            if not details:
                logger.warning(f"Could not fetch details for VOD {video_no}. Skipping.")
                continue

            vod_pydantic, _, _ = details
            publish_datetime = _parse_date_string(vod_pydantic.publish_date)

            # 필터링 로직
            if last_crawled_at and publish_datetime and publish_datetime <= last_crawled_at:
                logger.info(
                    f"VOD {video_no} ({publish_datetime}) is older than or same as last crawl time. Halting collection for this channel."
                )
                break

            # --- 루프 내 DB 작업: VOD 생성 ---
            with self.db_session_provider() as db:
                self._create_vod_in_session(db, channel_id, vod_pydantic)
                db.commit()  # VOD 하나 생성 후 즉시 커밋
                new_vod_count += 1
            # <-- VOD 생성용 세션은 여기서 즉시 닫힙니다.

        # --- 마지막 DB 작업: 채널의 마지막 스캔 시간 업데이트 ---
        with self.db_session_provider() as db:
            channel_repo = ChannelRepository(db)
            channel_repo.update_last_crawled_at(channel_id, datetime.now(UTC))
            db.commit()
        # <-- 마지막 DB 세션도 작업 후 즉시 닫힙니다.

        return processed_count, new_vod_count

    def _create_vod_in_session(self, db: Session, channel_id: str, vod_pydantic: ChzzkVodInfo):
        """
        주어진 DB 세션 내에서 Pydantic 모델로부터 VOD ORM 객체를 생성하고 저장합니다.
        """
        # VOD를 생성하려면 연관된 채널 객체가 필요하므로, 현재 세션 내에서 다시 조회합니다.
        channel_repo = ChannelRepository(db)
        channel_in_session = channel_repo.get_by_channel_id(channel_id)
        if not channel_in_session:
            # 이 경우는 거의 발생하지 않지만, 방어적으로 코딩합니다.
            raise RuntimeError(f"Channel {channel_id} disappeared during processing.")

        orm_columns = {c.key for c in ChzzkVodORM.__table__.columns}
        vod_data_to_save = vod_pydantic.model_dump(include=orm_columns)
        vod_data_to_save["publish_date"] = _parse_date_string(vod_pydantic.publish_date)
        vod_data_to_save["live_open_date"] = _parse_date_string(vod_pydantic.live_open_date)

        # Repository를 통해 VOD를 생성합니다.
        vod_repo = VodRepository(db)
        vod_repo.create(channel_in_session, vod_data_to_save)
        logger.info(f"Successfully created VOD '{vod_pydantic.video_title}' in DB.")
