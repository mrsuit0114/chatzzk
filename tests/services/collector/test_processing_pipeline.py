import types
from unittest.mock import patch

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chatzzk.packages.constants.service_codes import VodProcessStatus
from chatzzk.packages.data_access.database import Base
from chatzzk.packages.schemas.db_models import ChzzkChannelORM, ChzzkVodORM
from chatzzk.services.collector.jobs.tasks.processing import process_vod_to_context
from chatzzk.services.collector.settings import collector_settings

# 테스트용 DB 엔진 및 세션 설정
engine = create_engine(collector_settings.database_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def chzzk_api_mock(requests_mock):
    requests_mock.get(
        collector_settings.chzzk_api.vod_info_url_template.format(video_no="12345"),
        json={
            "content": {
                "videoNo": "12345",
                "videoTitle": "Test Video",
                "duration": 3600,
                "videoCategoryValue": "GAME",
                "channel": {"channelId": "test-channel-id"},
                "liveOpenDate": "2025-09-15 12:00:00",
                "publishDate": "2025-09-15 13:00:00",
                "videoId": "dummy-video-id",
                "inKey": "dummy-in-key",
            }
        },
    )
    requests_mock.get(
        collector_settings.chzzk_api.vod_url_template.format(video_id="dummy-video-id", in_key="dummy-in-key"),
        text='<MPD xmlns="urn:mpeg:dash:schema:mpd:2011"><Period><AdaptationSet><Representation height="480"><BaseURL>http://dummy.url/video.mp4</BaseURL></Representation></AdaptationSet></Period></MPD>',
    )
    requests_mock.get(
        collector_settings.chzzk_api.vod_chat_url_template.format(video_no="12345"),
        json={"content": {"videoChats": [], "nextPlayerMessageTime": None}},
    )


@patch("chatzzk.services.collector.jobs.tasks.processing.cleanup_workspace")
@patch("chatzzk.services.collector.jobs.tasks.processing.storage_manager")
@patch("chatzzk.services.collector.jobs.tasks.processing.merge_context_files", return_value=[])
@patch("chatzzk.services.collector.jobs.tasks.processing._perform_asr_and_create_context", return_value=[])
@patch("chatzzk.services.collector.jobs.tasks.processing.vad_client")
@patch("chatzzk.services.collector.jobs.tasks.processing.load_audio")
@patch("chatzzk.services.collector.jobs.tasks.processing.extract_wav_from_video")
@patch("chatzzk.services.collector.jobs.tasks.processing.download_file_from_url")
@patch("chatzzk.services.collector.jobs.tasks.processing.prepare_workspace")
def test_process_vod_pipeline_success(
    mock_prepare_workspace,
    mock_download,
    mock_extract_wav,
    mock_load_audio,
    mock_vad_client,
    mock_perform_asr,
    mock_merge_context,
    mock_storage_manager,
    mock_cleanup,
    db_session,
    chzzk_api_mock,
    tmp_path,  # <--- pytest의 tmp_path fixture 추가
):
    """..."""
    # 1. Arrange
    # prepare_workspace가 임시 경로를 담은 객체를 반환하도록 설정
    mock_paths = types.SimpleNamespace()
    mock_paths.mp4 = tmp_path / "video.mp4"
    mock_paths.wav = tmp_path / "audio.wav"
    mock_paths.chat_context = tmp_path / "chat.jsonl"
    mock_paths.asr_context = tmp_path / "asr.jsonl"
    mock_prepare_workspace.return_value = mock_paths

    mock_storage_manager.save_context.return_value = "mocked/path/to/context.jsonl"
    mock_load_audio.return_value = (np.empty(1), 16000)
    mock_vad_client.detect_speech.return_value = []

    test_channel = ChzzkChannelORM(id=1, channel_id="test-channel-id", channel_name="Test Channel")
    db_session.add(test_channel)
    db_session.commit()

    test_vod = ChzzkVodORM(
        video_no="12345", video_title="Test Video", process_status="PENDING", channel_pk=test_channel.id
    )
    db_session.add(test_vod)
    db_session.commit()

    # 2. Act
    process_vod_to_context(test_vod.id)

    # 3. Assert
    mock_prepare_workspace.assert_called_once_with("12345")
    mock_download.assert_called_once()
    mock_extract_wav.assert_called_once()
    mock_load_audio.assert_called_once()
    mock_vad_client.detect_speech.assert_called_once()
    mock_perform_asr.assert_called_once()
    mock_storage_manager.save_context.assert_called_once()
    mock_cleanup.assert_called_once_with("12345")

    db_session.refresh(test_vod)
    assert test_vod.process_status == VodProcessStatus.PROCESSING
    assert test_vod.analysis_result is not None
    assert test_vod.analysis_result.context_file_key == "mocked/path/to/context.jsonl"
