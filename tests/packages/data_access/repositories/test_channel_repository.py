from datetime import UTC, datetime

from sqlalchemy.orm import Session

from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.schemas.db_models import ChzzkChannelORM, PlatformORM


class TestChannelRepository:
    def test_get_or_create_new_channel(self, db_session: Session):
        """
        테스트 내용: DB에 존재하지 않는 채널에 대해 get_or_create를 호출합니다.
        테스트 목적: 새로운 채널이 DB에 올바르게 생성되는지 검증합니다.
        """
        platform = PlatformORM(id=1, platform_code="chzzk", platform_name="치지직")
        db_session.add(platform)
        db_session.commit()

        repo = ChannelRepository(db=db_session)
        channel_id = "newChannel123"
        channel_name = "새로운 채널"

        created_channel = repo.get_or_create(channel_id=channel_id, channel_name=channel_name, platform_id=platform.id)

        assert created_channel is not None
        assert created_channel.channel_id == channel_id
        assert created_channel.channel_name == channel_name
        assert created_channel.platform_id == platform.id

        db_channel = db_session.query(ChzzkChannelORM).filter_by(channel_id=channel_id).one_or_none()
        assert db_channel is not None
        assert db_channel.id == created_channel.id

    def test_get_or_create_existing_channel(self, db_session: Session):
        """
        테스트 내용: DB에 이미 존재하는 채널에 대해 get_or_create를 호출합니다.
        테스트 목적: 새로운 채널을 만들지 않고, 기존 채널을 올바르게 조회하는지 검증합니다.
        """
        platform = PlatformORM(id=1, platform_code="chzzk", platform_name="치지직")
        pre_existing_channel = ChzzkChannelORM(
            platform_id=platform.id, channel_id="existingChannel456", channel_name="기존 채널"
        )
        db_session.add(platform)
        db_session.add(pre_existing_channel)
        db_session.commit()
        original_id = pre_existing_channel.id

        repo = ChannelRepository(db=db_session)

        retrieved_channel = repo.get_or_create(
            channel_id="existingChannel456",
            channel_name="다른 이름의 채널",
            platform_id=platform.id,
        )

        assert retrieved_channel is not None
        assert retrieved_channel.id == original_id
        assert retrieved_channel.channel_name == "기존 채널"

        count = db_session.query(ChzzkChannelORM).count()
        assert count == 1

    def test_get_by_channel_id_found(self, db_session: Session):
        """channel_id로 조회 시, 정확한 채널을 반환하는지 검증합니다."""
        platform = PlatformORM(id=1, platform_code="chzzk", platform_name="치지직")
        target_channel = ChzzkChannelORM(platform_id=1, channel_id="find_me", channel_name="찾아줘")
        db_session.add(platform)
        db_session.add(target_channel)
        db_session.commit()

        repo = ChannelRepository(db=db_session)
        found_channel = repo.get_by_channel_id("find_me")

        assert found_channel is not None
        assert found_channel.id == target_channel.id

    def test_get_by_channel_id_not_found(self, db_session: Session):
        """존재하지 않는 channel_id로 조회 시, None을 반환하는지 검증합니다."""
        repo = ChannelRepository(db=db_session)
        found_channel = repo.get_by_channel_id("non_existent_id")
        assert found_channel is None

    def test_get_active_list(self, db_session: Session):
        """활성화된 채널 목록만 정확히 반환하는지 검증합니다."""
        platform = PlatformORM(id=1, platform_code="chzzk", platform_name="치지직")
        db_session.add(platform)
        db_session.commit()

        # 테스트 데이터 생성
        active_channel1 = ChzzkChannelORM(
            platform_id=1, channel_name="test-active1", channel_id="active1", allow_data_collection=True
        )
        inactive_channel = ChzzkChannelORM(
            platform_id=1, channel_name="test-inactive1", channel_id="inactive1", allow_data_collection=False
        )
        active_channel2 = ChzzkChannelORM(
            platform_id=1, channel_name="test-active2", channel_id="active2", allow_data_collection=True
        )
        db_session.add_all([active_channel1, inactive_channel, active_channel2])
        db_session.commit()

        repo = ChannelRepository(db=db_session)
        active_list = repo.get_active_list()

        assert len(active_list) == 2
        active_ids = {ch.channel_id for ch in active_list}
        assert "active1" in active_ids
        assert "active2" in active_ids
        assert "inactive1" not in active_ids

    def test_update_last_crawled_at(self, db_session: Session):
        """채널의 마지막 크롤링 시간을 정확히 갱신하는지 검증합니다."""
        platform = PlatformORM(id=1, platform_code="chzzk", platform_name="치지직")
        channel = ChzzkChannelORM(platform_id=1, channel_id="update_me", channel_name="test-update-me")
        db_session.add(platform)
        db_session.add(channel)
        db_session.commit()
        channel_id_to_update = channel.channel_id

        repo = ChannelRepository(db=db_session)
        crawl_time = datetime.now(UTC)

        repo.update_last_crawled_at(channel_id_to_update, crawl_time)

        # DB에서 직접 다시 조회하여 확인
        updated_channel = db_session.query(ChzzkChannelORM).filter_by(channel_id=channel_id_to_update).one()
        assert updated_channel.last_vod_crawled_at is not None
        # DB에 따라 미세한 정밀도 차이가 있을 수 있으므로, 초 단위까지만 비교
        assert updated_channel.last_vod_crawled_at.replace(microsecond=0) == crawl_time.replace(microsecond=0)
