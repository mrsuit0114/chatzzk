# tests/packages/utils/test_downloader.py

import tempfile
from pathlib import Path

import pytest
import requests

from chatzzk.packages.utils.downloader import download_file_from_url


def test_download_file_from_url_success(mocker):
    """
    목적: 네트워크에서 파일을 성공적으로 다운로드하여 로컬에 저장하는 핵심 "성공 경로"를 테스트합니다.
    이유: 함수의 가장 기본적인 기능이 올바르게 동작하는지 보장하기 위함입니다.
    """
    # 준비 (Arrange)
    # 1. 가짜 파일 내용과 URL을 준비합니다.
    fake_content = b"This is a fake mp4 file content."
    test_url = "http://fake.url/video.mp4"

    # 2. requests.get의 응답을 흉내내는 Mock 객체를 생성합니다.
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None  # HTTP 에러가 없도록 설정
    mock_response.headers = {"content-length": str(len(fake_content))}
    mock_response.iter_content.return_value = [fake_content]  # 청크 단위로 데이터를 반환

    # 3. requests.Session().get이 호출되면 위에서 만든 Mock 객체를 반환하도록 설정합니다.
    mock_session_get = mocker.patch(
        "requests.Session.get", return_value=mocker.MagicMock(__enter__=mocker.Mock(return_value=mock_response))
    )

    # 4. 파일을 저장할 임시 디렉토리를 생성합니다.
    with tempfile.TemporaryDirectory() as tmpdir:
        destination_path = Path(tmpdir) / "test_video.mp4"

        # 실행 (Act)
        # 테스트할 함수를 호출합니다.
        download_file_from_url(test_url, destination_path, show_progress=False)

        # 검증 (Assert)
        # 1. requests.get이 올바른 인자(URL, stream=True)로 호출되었는지 확인합니다.
        mock_session_get.assert_called_once_with(test_url, stream=True, timeout=300)

        # 2. 파일이 실제로 생성되었는지 확인합니다.
        assert destination_path.exists()

        # 3. 파일의 내용이 우리가 준비한 가짜 내용과 일치하는지 확인합니다.
        with open(destination_path, "rb") as f:
            content = f.read()
        assert content == fake_content


def test_download_file_from_url_http_error(mocker):
    """
    목적: 서버가 404, 500 등 에러 코드를 응답했을 때, 함수가 올바르게 실패하는지 테스트합니다.
    이유: 비정상적인 서버 응답을 정상적인 다운로드로 처리하지 않도록 방지하고, 실패 시 파일을 남기지 않는지 확인해야 합니다.
    """
    # 준비 (Arrange)
    test_url = "http://fake.url/not_found.mp4"

    # 1. raise_for_status()가 HTTPError를 발생시키도록 설정합니다.
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mocker.patch(
        "requests.Session.get", return_value=mocker.MagicMock(__enter__=mocker.Mock(return_value=mock_response))
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        destination_path = Path(tmpdir) / "test_video.mp4"

        # 실행 및 검증 (Act & Assert)
        # 2. ConnectionError가 발생하는지 확인합니다. (구현상 HTTPError를 ConnectionError로 감싸서 raise)
        with pytest.raises(ConnectionError):
            download_file_from_url(test_url, destination_path, show_progress=False)

        # 3. 실패했으므로, 부분적으로 다운로드된 파일이 없어야 합니다.
        assert not destination_path.exists()


def test_download_file_from_url_network_error(mocker):
    """
    목적: DNS 조회 실패, 타임아웃 등 네트워크 자체에 문제가 생겼을 때, 함수가 올바르게 실패하는지 테스트합니다.
    이유: 불안정한 네트워크 환경에서도 시스템이 안정적으로 동작하고, 예외 상황을 적절히 처리하는지 보장해야 합니다.
    """
    # 준비 (Arrange)
    test_url = "http://unreachable.url/video.mp4"

    # 1. requests.get 자체가 RequestException을 발생시키도록 설정합니다.
    mocker.patch("requests.Session.get", side_effect=requests.exceptions.RequestException)

    with tempfile.TemporaryDirectory() as tmpdir:
        destination_path = Path(tmpdir) / "test_video.mp4"

        # 실행 및 검증 (Act & Assert)
        # 2. ConnectionError가 발생하는지 확인합니다.
        with pytest.raises(ConnectionError):
            download_file_from_url(test_url, destination_path, show_progress=False)

        # 3. 실패했으므로, 파일이 생성되지 않았어야 합니다.
        assert not destination_path.exists()
