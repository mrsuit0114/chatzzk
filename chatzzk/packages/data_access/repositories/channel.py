from datetime import datetime

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from chatzzk.packages.schemas.db_models import ChzzkChannelORM


class ChannelRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_channel_id(self, channel_id: str) -> ChzzkChannelORM | None:
        """channel_id로 채널을 조회합니다."""
        return self.db.query(ChzzkChannelORM).filter(ChzzkChannelORM.channel_id == channel_id).first()

    def get_or_create_channel(
        self, channel_id: str, channel_name: str, platform_id: int
    ) -> tuple[ChzzkChannelORM, bool]:
        """
        channel_id로 채널을 조회하고, 없으면 새로 생성합니다.
        Race Condition 발생 시에도 멱등성을 보장합니다.
        :return: (채널 객체, 생성 여부 bool)
        """
        db_channel = self.get_by_channel_id(channel_id)
        if db_channel:
            return db_channel, False

        try:
            logger.info(f"Channel not found for channel_id: {channel_id}. Creating new one.")
            db_channel = ChzzkChannelORM(channel_id=channel_id, channel_name=channel_name, platform_id=platform_id)
            self.db.add(db_channel)
            self.db.commit()
            self.db.refresh(db_channel)
            logger.success(f"Successfully created channel: {channel_name} ({channel_id})")
            return db_channel, True
        except IntegrityError:  # 동시 생성 요청으로 인한 UNIQUE 제약조건 위반
            self.db.rollback()
            logger.warning(f"Race condition detected for channel {channel_id}. Re-fetching.")
            # 다른 워커가 먼저 생성했으므로, 다시 조회하여 반환
            db_channel = self.get_by_channel_id(channel_id)
            return db_channel, False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create channel {channel_name}: {e}")
            raise

    def get_active_list(self) -> list[ChzzkChannelORM]:
        """데이터 수집이 활성화된 모든 채널 목록을 반환합니다."""
        return self.db.query(ChzzkChannelORM).filter(ChzzkChannelORM.allow_data_collection).all()

    def update_last_crawled_at(
        self, channel_id: str, new_crawl_time: datetime, previous_crawl_time: datetime | None
    ) -> bool:
        """
        Lost Update 문제를 방지하기 위해 조건부 업데이트(낙관적 잠금)를 사용합니다.
        이전에 읽었던 crawl_time을 조건으로 넣어, 그 사이에 값이 변경되지 않았을 때만 업데이트합니다.
        :return: 업데이트 성공 시 True, 실패(충돌 발생) 시 False
        """
        try:
            query = self.db.query(ChzzkChannelORM).filter(ChzzkChannelORM.channel_id == channel_id)

            # 조건부 업데이트를 위한 WHERE 절 추가
            if previous_crawl_time is not None:
                query = query.filter(ChzzkChannelORM.last_vod_crawled_at == previous_crawl_time)
            else:
                query = query.filter(ChzzkChannelORM.last_vod_crawled_at.is_(None))

            result = query.update({"last_vod_crawled_at": new_crawl_time}, synchronize_session=False)

            self.db.commit()

            if result == 0:
                # 업데이트된 행이 0개 -> 다른 워커가 먼저 값을 변경했음 (충돌 발생)
                logger.warning(f"Optimistic lock failed for channel {channel_id}. Another worker may have updated it.")
                return False

            logger.success(f"Updated last_vod_crawled_at for channel {channel_id}.")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update last_vod_crawled_at for channel {channel_id}: {e}")
            raise
