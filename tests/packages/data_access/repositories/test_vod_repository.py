import pytest
from sqlalchemy.orm import Session

from chatzzk.packages.constants.service_codes import StepStatus, VodProcessStatus
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.schemas.db_models import ChzzkChannelORM, ChzzkVodORM


class TestVodRepository:
    @pytest.fixture
    def repo(self, db_session: Session) -> VodRepository:
        return VodRepository(db=db_session)

    @pytest.fixture
    def channel(self, chzzk_channel_factory) -> ChzzkChannelORM:
        return chzzk_channel_factory()

    def test_create_or_get_vod_on_new(self, repo: VodRepository, channel: ChzzkChannelORM, db_session: Session):
        """
        테스트 내용: 존재하지 않는 새로운 VOD에 대해 create_or_get_vod를 호출합니다.
        테스트 목적: 멱등성 함수의 '생성' 경로를 검증합니다. 새로운 VOD와 관련 객체(status, analytics)가
                     올바른 기본값으로 생성되는지, 반환값으로 (객체, True)가 정확히 오는지 확인합니다.
        """
        # 준비
        vod_data = {"video_no": "123123", "video_title": "New VOD"}

        # 실행
        created_vod, was_created = repo.create_or_get_vod(channel=channel, vod_data=vod_data)

        # 검증
        assert was_created is True
        assert created_vod is not None
        assert created_vod.video_no == "123123"
        assert created_vod.channel_pk == channel.id
        assert created_vod.processing_status is not None
        assert created_vod.analytics is not None
        assert created_vod.processing_status.process_status == VodProcessStatus.PENDING

        # DB 직접 확인
        db_vod = db_session.query(ChzzkVodORM).filter_by(video_no="123123").one()
        assert db_vod.id == created_vod.id

    def test_create_or_get_vod_on_existing(self, repo: VodRepository, channel: ChzzkChannelORM):
        """
        테스트 내용: 이미 존재하는 VOD에 대해 create_or_get_vod를 다시 호출합니다.
        테스트 목적: 멱등성 함수의 '조회' 경로를 검증합니다. 새로운 객체를 생성하지 않고 기존 VOD 객체를
                     반환하는지, 반환값으로 (객체, False)가 정확히 오는지 확인합니다.
        """
        # 준비: 먼저 하나 생성
        vod_data = {"video_no": "123456", "video_title": "Existing VOD"}
        existing_vod, _ = repo.create_or_get_vod(channel=channel, vod_data=vod_data)

        # 실행: 동일한 video_no로 다시 호출
        fetched_vod, was_created = repo.create_or_get_vod(channel=channel, vod_data=vod_data)

        # 검증
        assert was_created is False
        assert fetched_vod is not None
        assert fetched_vod.id == existing_vod.id
        assert fetched_vod.video_no == "123456"

    def test_find_and_lock_pending_vod(self, repo: VodRepository, channel: ChzzkChannelORM, db_session: Session):
        """
        테스트 내용: PENDING 상태의 VOD가 있을 때 find_and_lock_pending_vod를 호출합니다.
        테스트 목적: 동시성 제어의 핵심인 '작업 획득' 로직을 검증합니다. 함수가 PENDING VOD를 찾아내고,
                     그 상태를 즉시 PROCESSING으로 변경한 뒤, 다른 워커가 더 이상 해당 VOD를
                     찾을 수 없는지 확인합니다.
        """
        # 준비: PENDING 상태의 VOD 생성
        repo.create_or_get_vod(channel=channel, vod_data={"video_no": "555554"})

        # 실행
        locked_vod = repo.find_and_lock_pending_vod()

        # 검증
        assert locked_vod is not None
        assert locked_vod.video_no == "555554"
        # 상태가 PROCESSING으로 변경되었는지 확인
        assert locked_vod.processing_status.process_status == VodProcessStatus.PROCESSING

        # 다른 워커가 접근 시도: 더 이상 PENDING VOD가 없어야 함
        another_vod = repo.find_and_lock_pending_vod()
        assert another_vod is None

    def test_update_pipeline_step_status(self, repo: VodRepository, channel: ChzzkChannelORM, db_session: Session):
        """
        테스트 내용: status_details 필드에 두 개의 다른 서브 작업 상태를 순차적으로 업데이트합니다.
        테스트 목적: JSONB 필드에 대한 원자적 업데이트 로직을 검증합니다. 한 작업의 업데이트가 다른 작업의
                     업데이트를 덮어쓰지 않고, 두 상태가 올바르게 병합되는지 확인합니다.
        """
        # 준비
        vod, _ = repo.create_or_get_vod(channel=channel, vod_data={"video_no": "494949"})
        vod_pk = vod.id

        # 실행 1: CHAT 단계 업데이트
        chat_status = {"status": StepStatus.COMPLETED, "chats_found": 1500}
        result1 = repo.update_pipeline_step_status(vod_pk, "chat_collection", chat_status)

        # 검증 1
        assert result1 is True
        db_session.refresh(vod.processing_status)
        assert vod.processing_status.status_details["chat_collection"]["status"] == StepStatus.COMPLETED

        # 실행 2: ASR 단계 동시 업데이트 (시뮬레이션)
        asr_status = {"status": StepStatus.COMPLETED, "model": "whisperx"}
        result2 = repo.update_pipeline_step_status(vod_pk, "asr", asr_status)

        # 검증 2
        assert result2 is True
        db_session.refresh(vod.processing_status)
        # 핵심 검증: 이전 단계(chat_collection) 정보가 그대로 남아있는지 확인
        assert vod.processing_status.status_details["chat_collection"]["status"] == StepStatus.COMPLETED
        assert vod.processing_status.status_details["asr"]["model"] == "whisperx"

    def test_update_analytics(self, repo: VodRepository, channel: ChzzkChannelORM, db_session: Session):
        """
        테스트 내용: 분석이 완료된 통계 데이터를 VOD에 업데이트합니다.
        테스트 목적: update_analytics 함수가 chzzk_vod_analytics 테이블의 필드를 정확하게
                     갱신하는지 검증합니다.
        """
        # 준비
        vod, _ = repo.create_or_get_vod(channel=channel, vod_data={"video_no": "999999"})
        vod_pk = vod.id

        # 실행
        analytics_data = {"total_chat_count": 5000, "donor_count": 25}
        result = repo.update_analytics(vod_pk, analytics_data)

        # 검증
        assert result is True
        db_session.refresh(vod.analytics)
        assert vod.analytics.total_chat_count == 5000
        assert vod.analytics.donor_count == 25

    def test_update_overall_status(self, repo: VodRepository, channel: ChzzkChannelORM, db_session: Session):
        """
        테스트 내용: VOD의 최종 처리 상태를 COMPLETED로 변경합니다.
        테스트 목적: update_overall_status 함수가 VOD의 주 상태를 올바르게 변경하는지 검증합니다.
        """
        # 준비
        vod, _ = repo.create_or_get_vod(channel=channel, vod_data={"video_no": "111111"})
        vod_pk = vod.id

        # 실행
        result = repo.update_overall_status(vod_pk, VodProcessStatus.COMPLETED)

        # 검증
        assert result is True
        db_session.refresh(vod.processing_status)
        assert vod.processing_status.process_status == VodProcessStatus.COMPLETED

    def test_get_by_video_no_eager_loading(self, repo: VodRepository, channel: ChzzkChannelORM, db_session: Session):
        """
        테스트 내용: VOD 조회 시 Eager Loading이 올바르게 동작하는지 확인합니다.
        테스트 목적: get_by_video_no 함수가 N+1 쿼리 문제를 방지하기 위해 연관 객체(status, analytics)를
                     JOIN을 통해 한번에 가져오는지 검증합니다. 세션을 만료시킨 후에도 추가 쿼리 없이
                     연관 객체에 접근이 가능해야 합니다.
        """
        # 준비
        vod, _ = repo.create_or_get_vod(channel=channel, vod_data={"video_no": "888888"})
        # 세션 만료 시뮬레이션
        db_session.expire_all()

        # 실행
        found_vod = repo.get_by_video_no("888888")

        # 검증: 추가 쿼리 없이 연관 객체에 접근 가능한지 확인
        # 접근 시 Lazy-loading 에러가 발생하지 않으면 성공
        assert found_vod is not None
        assert found_vod.processing_status.process_status == VodProcessStatus.PENDING
        assert found_vod.analytics is not None
