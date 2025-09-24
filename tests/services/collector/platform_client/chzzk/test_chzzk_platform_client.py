import pytest
from requests_mock import Mocker

from chatzzk.packages.schemas.data_models import ChzzkChannelInfo, ChzzkVodInfo
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)
from chatzzk.services.collector.settings import collector_settings


class TestChzzkPlatformClient:
    @pytest.fixture
    def client(self) -> ChzzkPlatformClient:
        """테스트를 위한 ChzzkPlatformClient 인스턴스를 생성합니다."""
        return ChzzkPlatformClient()

    def test_fetch_vod_details_success(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: API가 성공적으로 예상된 데이터를 반환하는 상황을 시뮬레이션합니다.
        테스트 목적: 이 'Happy Path'(이상적인 시나리오)에서 클라이언트가 JSON 데이터를 정확히 파싱하여,
                    우리가 원하는 ChzzkVodInfo 객체와 videoId, inKey가 담긴 튜플을 올바르게 만들어내는지 검증합니다.
        """
        video_no = "12345"
        channel_id = "testChannel123"
        api_url = collector_settings.chzzk_api.vod_info_url_template.format(video_no=video_no)

        mock_response_data = {
            "code": 200,
            "message": None,
            "content": {
                "videoNo": video_no,
                "videoTitle": "테스트 VOD 제목",
                "duration": 3600,
                "videoCategoryValue": "GAME",
                "channel": {"channelId": channel_id},
                "liveOpenDate": "2025-01-01 12:00:00",
                "publishDate": "2025-01-01 15:00:00",
                "videoId": "V-12345-67890",
                "inKey": "some_secret_inkey",
            },
        }
        requests_mock.get(api_url, json=mock_response_data)

        result = client.fetch_vod_details(video_no)

        assert result is not None
        vod_info, video_id, in_key = result

        assert isinstance(vod_info, ChzzkVodInfo)
        assert vod_info.video_no == video_no
        assert vod_info.video_title == "테스트 VOD 제목"
        assert vod_info.channel_id == channel_id
        assert video_id == "V-12345-67890"
        assert in_key == "some_secret_inkey"

    def test_fetch_vod_details_api_error(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: API가 404 Not Found 같은 에러를 반환하는 상황을 시뮬레이션합니다.
        테스트 목적: 견고한 실패 처리 능력을 검증합니다. 클라이언트가 프로그램 전체를 멈추는 예외를 던지는 대신,
                    API 통신 실패를 인지하고 None을 반환하여 호출자가 안전하게 다음 작업을 이어갈 수 있도록 하는지를 확인합니다.
        """
        video_no = "12345"
        api_url = collector_settings.chzzk_api.vod_info_url_template.format(video_no=video_no)
        requests_mock.get(api_url, status_code=404)

        result = client.fetch_vod_details(video_no)

        assert result is None

    def test_fetch_vod_details_missing_keys(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: API 통신은 성공했지만, 응답 데이터의 내용 중 필수적인 'inKey' 같은 필드가 누락된 상황을 시뮬레이션합니다.
        테스트 목적: 방어적인 동작을 검증합니다. 이처럼 예상치 못한 데이터 구조에 대해서도 클라이언트가 비정상 종료되지 않고,
                    데이터가 불완전함을 스스로 인지하여 None을 반환하는지를 확인합니다.
        """
        video_no = "12345"
        api_url = collector_settings.chzzk_api.vod_info_url_template.format(video_no=video_no)

        mock_response_data = {
            "code": 200,
            "message": None,
            "content": {
                "videoNo": video_no,
                "videoTitle": "키가 누락된 VOD",
                "videoId": "V-54321-09876",
            },
        }
        requests_mock.get(api_url, json=mock_response_data)

        result = client.fetch_vod_details(video_no)

        assert result is None

    def test_crawl_chat_success_with_pagination(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: 채팅이 여러 페이지에 걸쳐 있는 상황을 시뮬레이션합니다.
        테스트 목적: 클라이언트가 페이지네이션(Pagination) 로직을 올바르게 따라가 모든 페이지의 채팅을
                    빠짐없이 수집하여 하나의 리스트로 합치는지 검증합니다.
        """
        video_no = "12345"
        base_url = collector_settings.chzzk_api.vod_chat_url_template.format(video_no=video_no)

        # 1페이지 Mock 응답
        requests_mock.get(
            f"{base_url}?playerMessageTime=0",
            json={
                "content": {
                    "videoChats": [
                        {
                            "messageTypeCode": 1,
                            "playerMessageTime": 1000,
                            "content": "채팅 1",
                        }
                    ],
                    "nextPlayerMessageTime": 1000,
                }
            },
        )
        # 2페이지 Mock 응답
        requests_mock.get(
            f"{base_url}?playerMessageTime=1000",
            json={
                "content": {
                    "videoChats": [
                        {
                            "messageTypeCode": 1,
                            "playerMessageTime": 1600,
                            "content": "채팅 2",
                        }
                    ],
                    "nextPlayerMessageTime": None,
                }
            },
        )

        results = client.crawl_chat(video_no)

        assert len(results) == 2
        assert results[0].content == "채팅 1"
        assert results[1].content == "채팅 2"
        assert requests_mock.call_count == 2

    def test_crawl_chat_no_chats(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: VOD에 채팅 기록이 전혀 없는 상황을 시뮬레이션합니다.
        테스트 목적: 채팅이 없을 경우, 클라이언트가 에러 없이 비어있는 리스트(`[]`)를 정상적으로 반환하는지 검증합니다.
        """
        video_no = "12345"
        api_url = collector_settings.chzzk_api.vod_chat_url_template.format(video_no=video_no)
        requests_mock.get(
            f"{api_url}?playerMessageTime=0",
            json={"content": {"videoChats": [], "nextPlayerMessageTime": None}},
        )

        results = client.crawl_chat(video_no)

        assert results == []
        assert requests_mock.call_count == 1

    def test_crawl_chat_api_error_during_pagination(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: 첫 페이지는 성공, 두 번째 페이지 요청에서 서버 에러가 발생하는 상황을 시뮬레이션합니다.
        테스트 목적: 불완전한 데이터 수집을 방지하기 위해, 작업이 온전히 성공하지 못했음을 알리는
                    `RuntimeError` 예외를 발생하는지 검증합니다.
        """
        video_no = "12345"
        base_url = collector_settings.chzzk_api.vod_chat_url_template.format(video_no=video_no)

        # 1페이지 (성공)
        requests_mock.get(
            f"{base_url}?playerMessageTime=0",
            json={
                "content": {
                    "videoChats": [
                        {
                            "messageTypeCode": 1,
                            "playerMessageTime": 1000,
                            "content": "채팅 1",
                        }
                    ],
                    "nextPlayerMessageTime": 1000,
                }
            },
        )
        # 2페이지 (실패)
        requests_mock.get(f"{base_url}?playerMessageTime=1000", status_code=500)

        with pytest.raises(RuntimeError, match="API request failed"):
            client.crawl_chat(video_no)

    def test_stream_all_video_numbers_success(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: VOD 목록이 여러 페이지에 걸쳐 있는 상황을 시뮬레이션합니다.
        테스트 목적: 클라이언트가 페이지네이션을 따라 모든 페이지의 VOD 번호를 빠짐없이 `yield`하는지 검증합니다.
        """
        channel_id = "testChannel001"
        template = collector_settings.chzzk_api.channel_vods_url_template

        requests_mock.get(
            template.format(channel_id=channel_id, page_idx=0),
            json={"content": {"data": [{"videoNo": 10101}, {"videoNo": 10102}]}},
        )
        requests_mock.get(
            template.format(channel_id=channel_id, page_idx=1), json={"content": {"data": [{"videoNo": 20202}]}}
        )
        requests_mock.get(template.format(channel_id=channel_id, page_idx=2), json={"content": {"data": []}})

        # 제너레이터를 리스트로 변환하여 모든 결과를 소진
        results = list(client.stream_all_video_numbers(channel_id))

        assert len(results) == 3
        assert results == ["10101", "10102", "20202"]
        assert requests_mock.call_count == 3

    def test_stream_all_video_numbers_no_vods(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: VOD가 하나도 없는 채널을 시뮬레이션합니다.
        테스트 목적: 첫 페이지 응답이 비어있을 경우, 제너레이터가 아무것도 `yield`하지 않고 정상 종료되는지 검증합니다.
        """
        channel_id = "testChannel002"
        api_url = collector_settings.chzzk_api.channel_vods_url_template.format(channel_id=channel_id, page_idx=0)
        requests_mock.get(api_url, json={"content": {"data": []}})

        results = list(client.stream_all_video_numbers(channel_id))

        assert results == []
        assert requests_mock.call_count == 1

    def test_stream_all_video_numbers_api_error(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: 페이지네이션 도중 API 에러가 발생하는 상황을 시뮬레이션합니다.
        테스트 목적: 에러 발생 시 예외를 발생시키지 않고, 에러 직전까지 수집된 VOD 번호들만 `yield`하고
                    스트리밍이 정상적으로 종료되는지 검증합니다.
        """
        channel_id = "testChannel003"
        template = collector_settings.chzzk_api.channel_vods_url_template

        requests_mock.get(
            template.format(channel_id=channel_id, page_idx=0), json={"content": {"data": [{"videoNo": 12345}]}}
        )
        requests_mock.get(template.format(channel_id=channel_id, page_idx=1), status_code=500)

        results = list(client.stream_all_video_numbers(channel_id))

        assert results == ["12345"]  # 성공한 첫 페이지만 결과에 포함
        # page 0 성공(1) + page 1 실패(최초 1 + 재시도 2 = 3) = 총 4번 호출
        assert requests_mock.call_count == 4

    def test_fetch_all_stream_representations_success(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: 유효한 DASH manifest (XML)가 반환되는 상황을 시뮬레이션합니다.
        테스트 목적: 클라이언트가 XML을 파싱하여 해상도와 URL을 추출하고, 해상도 기준으로 정렬된 리스트를 반환하는지 검증합니다.
        """
        video_id, in_key = "V-123", "some-key"
        api_url = collector_settings.chzzk_api.vod_url_template.format(video_id=video_id, in_key=in_key)
        mock_xml_data = """
        <MPD xmlns="urn:mpeg:dash:schema:mpd:2011">
            <Period>
                <AdaptationSet>
                    <Representation height="1080">
                        <BaseURL>https://example.com/1080p.m4s</BaseURL>
                    </Representation>
                    <Representation height="480">
                        <BaseURL>https://example.com/480p.m4s</BaseURL>
                    </Representation>
                    <Representation height="720">
                        <BaseURL>https://example.com/720p.m4s</BaseURL>
                    </Representation>
                </AdaptationSet>
            </Period>
        </MPD>
        """
        requests_mock.get(api_url, text=mock_xml_data)
        result = client.fetch_all_stream_representations(video_id, in_key)
        assert result is not None
        assert len(result) == 3
        # 해상도 오름차순으로 정렬되었는지 확인
        assert result[0] == (480, "https://example.com/480p.m4s")
        assert result[2] == (1080, "https://example.com/1080p.m4s")

    def test_fetch_all_stream_representations_parsing_error(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: API 응답이 깨진 XML일 경우를 시뮬레이션합니다.
        테스트 목적: XML 파싱 에러 발생 시, 함수가 비정상 종료되지 않고 `None`을 반환하며 안전하게 실패하는지 검증합니다.
        """
        video_id, in_key = "V-456", "some-key"
        api_url = collector_settings.chzzk_api.vod_url_template.format(video_id=video_id, in_key=in_key)
        requests_mock.get(api_url, text="<MPD><UnclosedTag>")
        result = client.fetch_all_stream_representations(video_id, in_key)
        assert result is None

    def test_fetch_all_stream_representations_api_error(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: API 자체가 404 에러를 반환하는 상황을 시뮬레이션합니다.
        테스트 목적: API 통신 실패 시, 함수가 예외 대신 `None`을 반환하며 안전하게 종료되는지 검증합니다.
        """
        video_id, in_key = "V-789", "some-key"
        api_url = collector_settings.chzzk_api.vod_url_template.format(video_id=video_id, in_key=in_key)
        requests_mock.get(api_url, status_code=404)

        result = client.fetch_all_stream_representations(video_id, in_key)

        assert result is None

    def test_fetch_channel_details_success(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: API가 유효한 채널 정보를 반환하는 상황을 시뮬레이션합니다.
        테스트 목적: 클라이언트가 JSON 데이터를 `ChzzkChannelInfo` Pydantic 모델로 정확히 파싱하는지 검증합니다.
        """
        channel_id = "testChannel999"
        api_url = collector_settings.chzzk_api.channel_info_url_template.format(channel_id=channel_id)
        mock_response = {
            "content": {
                "channelId": channel_id,
                "channelName": "테스트 채널 999",
                "verifiedMark": True,
                "followerCount": 12345,
                "openLive": False,
            }
        }
        requests_mock.get(api_url, json=mock_response)
        result = client.fetch_channel_details(channel_id)
        assert isinstance(result, ChzzkChannelInfo)
        assert result.channel_id == channel_id
        assert result.follower_count == 12345

    def test_fetch_channel_details_api_error(self, client: ChzzkPlatformClient, requests_mock: Mocker):
        """
        테스트 내용: 존재하지 않는 채널 ID로 요청하여 API가 404 에러를 반환하는 상황을 시뮬레이션합니다.
        테스트 목적: 이 경우에도 함수가 비정상 종료되지 않고, `None`을 반환하며 안전하게 실패하는지 검증합니다.
        """
        channel_id = "nonExistentChannel"
        api_url = collector_settings.chzzk_api.channel_info_url_template.format(channel_id=channel_id)
        requests_mock.get(api_url, status_code=404)
        result = client.fetch_channel_details(channel_id)
        assert result is None
