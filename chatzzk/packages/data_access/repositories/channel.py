from datetime import datetime

from loguru import logger
from sqlalchemy.orm import Session

from chatzzk.packages.schemas.db_models import ChzzkChannelORM


class ChannelRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_channel_id(self, channel_id: str) -> ChzzkChannelORM | None:
        """channel_id로 채널을 조회합니다."""
        return self.db.query(ChzzkChannelORM).filter(ChzzkChannelORM.channel_id == channel_id).first()

    def get_or_create(self, channel_id: str, channel_name: str) -> ChzzkChannelORM:
        """channel_id로 채널을 조회하고, 없으면 새로 생성합니다."""
        db_channel = self.get_by_channel_id(channel_id)
        if not db_channel:
            logger.info(f"Channel not found for channel_id: {channel_id}. Creating new one.")
            db_channel = ChzzkChannelORM(channel_id=channel_id, channel_name=channel_name)
            try:
                self.db.add(db_channel)
                self.db.commit()
                self.db.refresh(db_channel)
                logger.success(f"Successfully created channel: {channel_name} ({channel_id})")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to create channel {channel_name}: {e}")
                raise
        return db_channel

    def get_active_list(self) -> list[ChzzkChannelORM]:
        """데이터 수집이 활성화된 모든 채널 목록을 반환합니다."""
        return self.db.query(ChzzkChannelORM).filter(ChzzkChannelORM.is_active).all()

    def update_last_crawled_at(self, channel_id: str, crawl_time: datetime):
        """채널의 마지막 VOD 수집 시간을 업데이트합니다."""
        try:
            channel = self.get_by_channel_id(channel_id)
            if channel:
                channel.last_vod_crawled_at = crawl_time
                self.db.commit()
                logger.success(f"Updated last_vod_crawled_at for channel {channel_id}.")
            else:
                logger.warning(f"Could not update last_vod_crawled_at. Channel {channel_id} not found.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update last_vod_crawled_at for channel {channel_id}: {e}")
            raise
