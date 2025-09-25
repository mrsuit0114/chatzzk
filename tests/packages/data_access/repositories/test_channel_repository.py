from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.schemas.db_models import PlatformORM


class TestChannelRepository:
    @pytest.fixture
    def repo(self, db_session: Session) -> ChannelRepository:
        return ChannelRepository(db=db_session)

    @pytest.fixture
    def platform(self, db_session: Session) -> PlatformORM:
        """각 테스트를 위한 플랫폼 객체를 생성합니다."""
        platform = PlatformORM(id=1, platform_code="chzzk", platform_name="치지직")
        db_session.add(platform)
        db_session.commit()
        return platform

    def test_get_or_create_channel_on_new(self, repo: ChannelRepository, platform: PlatformORM):
        """
        테스트 내용: 존재하지 않는 채널에 대해 get_or_create_channel을 호출합니다.
        테스트 목적: 새로운 채널이 DB에 올바르게 생성되고, (객체, True)를 반환하는지 검증합니다.
        """
        # 실행
        created_channel, was_created = repo.get_or_create_channel(
            channel_id="new_channel_1", channel_name="새로운 채널", platform_id=platform.id
        )

        # 검증
        assert was_created is True
        assert created_channel is not None
        assert created_channel.channel_id == "new_channel_1"

    def test_get_or_create_channel_on_existing(self, repo: ChannelRepository, platform: PlatformORM):
        """
        테스트 내용: 이미 존재하는 채널에 대해 get_or_create_channel을 다시 호출합니다.
        테스트 목적: 새로운 객체를 만들지 않고 기존 객체를 반환하며, (객체, False)를 반환하는지 검증합니다.
        """
        # 준비: 먼저 하나 생성
        existing_channel, _ = repo.get_or_create_channel(
            channel_id="existing_channel_1", channel_name="기존 채널", platform_id=platform.id
        )

        # 실행
        fetched_channel, was_created = repo.get_or_create_channel(
            channel_id="existing_channel_1", channel_name="다른 이름", platform_id=platform.id
        )

        # 검증
        assert was_created is False
        assert fetched_channel.id == existing_channel.id

    def test_update_last_crawled_at_success(self, repo: ChannelRepository, platform: PlatformORM, db_session: Session):
        """
        테스트 내용: 정상적인 상황에서 마지막 크롤링 시간을 업데이트합니다.
        테스트 목적: 조건부 업데이트가 성공하고, DB에 시간이 올바르게 기록되는지 검증합니다.
        """
        # 준비
        channel, _ = repo.get_or_create_channel(
            channel_id="update_success", channel_name="업데이트 성공", platform_id=platform.id
        )
        previous_time = channel.last_vod_crawled_at
        assert previous_time is None

        # 실행
        new_time = datetime.now(UTC)
        result = repo.update_last_crawled_at(channel.channel_id, new_time, previous_time)

        # 검증
        assert result is True
        db_session.refresh(channel)
        assert channel.last_vod_crawled_at.replace(microsecond=0) == new_time.replace(microsecond=0)

    def test_update_last_crawled_at_conflict(self, repo: ChannelRepository, platform: PlatformORM, db_session: Session):
        """
        테스트 내용: 다른 워커가 먼저 값을 변경한 상황(Lost Update)을 시뮬레이션합니다.
        테스트 목적: 조건부 업데이트가 실패하고, False를 반환하며, DB 값이 덮어써지지 않는지 검증합니다.
        """
        # 준비
        channel, _ = repo.get_or_create_channel(
            channel_id="update_conflict", channel_name="업데이트 충돌", platform_id=platform.id
        )
        stale_previous_time = channel.last_vod_crawled_at  # 워커 A가 읽은 낡은 시간 (None)
        assert stale_previous_time is None

        # 시뮬레이션: 워커 B가 먼저 DB 값을 변경함
        actual_db_time = datetime.now(UTC)
        channel.last_vod_crawled_at = actual_db_time
        db_session.commit()
        db_session.refresh(channel)

        # 실행: 워커 A가 낡은 시간(None)을 기준으로 업데이트 시도
        new_time_for_a = datetime.now(UTC) + timedelta(seconds=10)
        result = repo.update_last_crawled_at(channel.channel_id, new_time_for_a, stale_previous_time)

        # 검증
        assert result is False  # 업데이트가 실패해야 함
        db_session.refresh(channel)
        # DB 값은 워커 B가 변경한 시간으로 유지되어야 함 (덮어쓰기 방지)
        assert channel.last_vod_crawled_at.replace(microsecond=0) == actual_db_time.replace(microsecond=0)
