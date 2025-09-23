from chatzzk.packages.schemas.data_models import ChzzkVodInfo
from chatzzk.packages.schemas.db_models import ChzzkVodORM


def test_discover_and_save_new_vods(test_container, db_session, chzzk_channel_factory):
    """
    새로운 VOD를 성공적으로 탐색하고 DB에 저장하는 시나리오를 테스트합니다.
    """
    # --- 1. Arrange (준비) ---
    channel = chzzk_channel_factory(channel_id="test_channel_123")

    mock_chzzk_client = test_container.chzzk_client()

    def stream_gen():
        yield from ["1001", "1002", "1003"]

    mock_chzzk_client.stream_all_video_numbers.return_value = stream_gen()

    mock_chzzk_client.fetch_vod_details.side_effect = [
        (
            ChzzkVodInfo(
                video_no="1001",
                video_title="영상1",
                duration=100,
                video_category_value="게임",
                channel={"channelId": channel.channel_id},
                live_open_date="2025-09-20 19:00:00",
                publish_date="2025-09-20 20:00:00",
            ),
            "vid1",
            "key1",
        ),
        (
            ChzzkVodInfo(
                video_no="1002",
                video_title="영상2",
                duration=200,
                video_category_value="게임",
                channel={"channelId": channel.channel_id},
                live_open_date="2025-09-21 19:00:00",
                publish_date="2025-09-21 20:00:00",
            ),
            "vid2",
            "key2",
        ),
        (
            ChzzkVodInfo(
                video_no="1003",
                video_title="영상3",
                duration=300,
                video_category_value="게임",
                channel={"channelId": channel.channel_id},
                live_open_date="2025-09-22 19:00:00",
                publish_date="2025-09-22 20:00:00",
            ),
            "vid3",
            "key3",
        ),
    ]
    # --- 2. Act (실행) ---
    discovery_service = test_container.vod_discovery_service()
    processed_count, new_vod_count = discovery_service.discover_and_save_new_vods(channel_id=channel.channel_id)
    # --- 3. Assert (검증) ---
    assert processed_count == 3
    assert new_vod_count == 3

    from chatzzk.packages.data_access.repositories.vod import VodRepository

    vods_in_db = VodRepository(db_session).db.query(ChzzkVodORM).all()
    assert len(vods_in_db) == 3
    assert vods_in_db[0].video_no == "1001"
    assert vods_in_db[1].video_title == "영상2"

    mock_chzzk_client.stream_all_video_numbers.assert_called_once_with(channel.channel_id)
    assert mock_chzzk_client.fetch_vod_details.call_count == 3
