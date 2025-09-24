from sqlalchemy.orm import Session

from chatzzk.packages.constants.service_codes import (
    PIPELINE_STATUS_KEY,
    PipelineStep,
    StepStatus,
    VodProcessStatus,
)
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.schemas.db_models import ChzzkVodORM


class TestVodRepository:
    def test_create(self, db_session: Session, chzzk_channel_factory):
        """
        테스트 내용: 새로운 VOD 데이터를 가지고 create 메서드를 호출합니다.
        테스트 목적: VOD 레코드가 올바른 기본값(특히 process_status)과 함께 DB에 잘 생성되는지 검증합니다.
        """
        # 준비 (Arrange)
        channel = chzzk_channel_factory()
        repo = VodRepository(db=db_session)
        vod_data = {
            "video_no": "123456789",
            "video_title": "테스트 VOD",
            "duration": 7200,
        }

        # 실행 (Act)
        created_vod = repo.create(channel=channel, vod_data=vod_data)

        # 검증 (Assert)
        assert created_vod is not None
        assert created_vod.video_no == "123456789"
        assert created_vod.video_title == "테스트 VOD"
        assert created_vod.channel_pk == channel.id
        # 핵심 검증: 기본 상태가 PENDING 인지 확인
        assert created_vod.process_status == VodProcessStatus.PENDING

        # DB에 실제로 데이터가 쓰였는지 다시 조회하여 확인
        db_vod = db_session.query(ChzzkVodORM).filter_by(video_no="123456789").one()
        assert db_vod.id == created_vod.id

    def test_get_list_to_process(self, db_session: Session, chzzk_channel_factory):
        """
        테스트 내용: 다양한 상태의 VOD가 있는 상황에서 get_list_to_process를 호출합니다.
        테스트 목적: PENDING과 FAILED 상태의 VOD만 정확히 조회하는지 검증합니다.
        """
        # 준비 (Arrange)
        channel = chzzk_channel_factory()
        vods_to_create = [
            ChzzkVodORM(channel_pk=channel.id, video_no="1", process_status=VodProcessStatus.PENDING),
            ChzzkVodORM(channel_pk=channel.id, video_no="2", process_status=VodProcessStatus.PROCESSING),
            ChzzkVodORM(channel_pk=channel.id, video_no="3", process_status=VodProcessStatus.COMPLETED),
            ChzzkVodORM(channel_pk=channel.id, video_no="4", process_status=VodProcessStatus.FAILED),
        ]
        db_session.add_all(vods_to_create)
        db_session.commit()

        repo = VodRepository(db=db_session)

        # 실행 (Act)
        vods_to_process = repo.get_list_to_process()

        # 검증 (Assert)
        assert len(vods_to_process) == 2
        video_nos_to_process = {vod.video_no for vod in vods_to_process}
        assert "1" in video_nos_to_process
        assert "4" in video_nos_to_process
        assert "2" not in video_nos_to_process
        assert "3" not in video_nos_to_process

    def test_update_process_status(self, db_session: Session, chzzk_channel_factory):
        """
        테스트 내용: VOD의 전체 처리 상태를 PENDING에서 PROCESSING으로 변경합니다.
        테스트 목적: process_status 필드가 DB에 정확하게 갱신되는지 검증합니다.
        """
        # 준비 (Arrange)
        channel = chzzk_channel_factory()
        vod = ChzzkVodORM(channel_pk=channel.id, video_no="1", process_status=VodProcessStatus.PENDING)
        db_session.add(vod)
        db_session.commit()

        repo = VodRepository(db=db_session)

        # 실행 (Act)
        result = repo.update_process_status(vod, VodProcessStatus.PROCESSING)

        # 검증 (Assert)
        assert result is True
        db_session.refresh(vod)  # 세션의 객체 상태를 DB와 동기화
        assert vod.process_status == VodProcessStatus.PROCESSING

    def test_update_pipeline_step(self, db_session: Session, chzzk_channel_factory):
        """
        테스트 내용: status_details(JSONB) 필드에 단계별 처리 상태를 순차적으로 기록합니다.
        테스트 목적: JSONB 필드가 덮어쓰이지 않고 올바르게 갱신되는지 검증합니다.
        """
        # 준비 (Arrange)
        channel = chzzk_channel_factory()
        vod = ChzzkVodORM(channel_pk=channel.id, video_no="1")
        db_session.add(vod)
        db_session.commit()

        repo = VodRepository(db=db_session)

        # 실행 1: 첫 번째 단계 기록
        repo.update_pipeline_step(vod, PipelineStep.CRAWL_CHAT, StepStatus.COMPLETED, metadata={"chats_found": 123})
        db_session.refresh(vod)

        # 검증 1
        assert vod.status_details[PipelineStep.CRAWL_CHAT][PIPELINE_STATUS_KEY] == StepStatus.COMPLETED
        assert vod.status_details[PipelineStep.CRAWL_CHAT]["chats_found"] == 123

        # 실행 2: 두 번째 단계 기록
        repo.update_pipeline_step(vod, PipelineStep.DOWNLOAD_VIDEO, StepStatus.COMPLETED)
        db_session.refresh(vod)

        # 검증 2
        assert vod.status_details[PipelineStep.DOWNLOAD_VIDEO][PIPELINE_STATUS_KEY] == StepStatus.COMPLETED
        # 핵심 검증: 이전 단계의 정보가 그대로 남아있는지 확인
        assert vod.status_details[PipelineStep.CRAWL_CHAT][PIPELINE_STATUS_KEY] == StepStatus.COMPLETED

    def test_get_by_video_no(self, db_session: Session, chzzk_channel_factory):
        """video_no로 VOD를 정확히 조회하고, 없을 때 None을 반환하는지 검증합니다."""
        channel = chzzk_channel_factory()
        vod = ChzzkVodORM(channel_pk=channel.id, video_no="111222")
        db_session.add(vod)
        db_session.commit()

        repo = VodRepository(db=db_session)

        # 찾았을 때
        found_vod = repo.get_by_video_no("111222")
        assert found_vod is not None
        assert found_vod.id == vod.id

        # 못 찾았을 때
        not_found_vod = repo.get_by_video_no("000000")
        assert not_found_vod is None

    def test_get_by_pk(self, db_session: Session, chzzk_channel_factory):
        """기본 키(PK)로 VOD를 정확히 조회하는지 검증합니다."""
        channel = chzzk_channel_factory()
        vod = ChzzkVodORM(channel_pk=channel.id, video_no="333444")
        db_session.add(vod)
        db_session.commit()
        vod_pk = vod.id

        repo = VodRepository(db=db_session)

        # 찾았을 때
        found_vod = repo.get_by_pk(vod_pk)
        assert found_vod is not None
        assert found_vod.video_no == "333444"

        # 못 찾았을 때
        not_found_vod = repo.get_by_pk(999999)
        assert not_found_vod is None
