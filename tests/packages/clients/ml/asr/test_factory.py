from unittest.mock import AsyncMock, patch

import pytest

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.clients.ml.asr.asr_http_client import ASRHttpClient
from chatzzk.packages.clients.ml.asr.factory import create_asr_client
from chatzzk.packages.clients.ml.asr.whisperx_client import WhisperxClient
from chatzzk.packages.schemas.config.ml import ASRHttpConfig, WhisperXConfig


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """`BaseHttpClient`의 AsyncMock 객체를 생성합니다."""
    return AsyncMock(spec=BaseHttpClient)


@pytest.fixture
def whisperx_config() -> WhisperXConfig:
    """테스트용 `WhisperXConfig` 객체를 생성합니다."""
    return WhisperXConfig(asr_implementation="whisperx", model_size="tiny")


@pytest.fixture
def asr_http_config() -> ASRHttpConfig:
    """테스트용 `ASRHttpConfig` 객체를 생성합니다."""
    return ASRHttpConfig(asr_implementation="http", asr_inference_server_url="http://mock")


# whisperx.load_model 호출을 막기 위해 patch 사용
@patch("whisperx.load_model")
def test_create_asr_client_with_whisperx_config(mock_load_model, whisperx_config):
    """
    목적: WhisperXConfig가 주어졌을 때, 팩토리가 WhisperxClient 인스턴스를 생성하는지 테스트합니다.
    """
    client = create_asr_client(model_config=whisperx_config)
    assert isinstance(client, WhisperxClient)


def test_create_asr_client_with_http_config(asr_http_config, mock_http_client):
    """
    목적: ASRHttpConfig와 http_client가 주어졌을 때, 팩토리가 ASRHttpClient 인스턴스를 생성하는지 테스트합니다.
    """
    client = create_asr_client(model_config=asr_http_config, http_client=mock_http_client)
    assert isinstance(client, ASRHttpClient)


def test_create_asr_client_with_http_config_missing_client_raises_error(asr_http_config):
    """
    목적: ASRHttpConfig 사용 시 http_client를 전달하지 않으면 ValueError가 발생하는지 테스트합니다.
    """
    with pytest.raises(ValueError, match="http_client must be provided for ASRHttpClient"):
        create_asr_client(model_config=asr_http_config)  # http_client 누락


def test_create_asr_client_with_unsupported_config_raises_error():
    """
    목적: 지원하지 않는 config 타입이 주어졌을 때, TypeError가 발생하는지 테스트합니다.
    """
    # Pydantic 모델이 아닌 일반 객체를 사용하여 테스트
    unsupported_config = type("UnsupportedConfig", (), {"asr_implementation": "unknown"})()

    with pytest.raises(TypeError, match="Unsupported ASR config type"):
        create_asr_client(model_config=unsupported_config)
