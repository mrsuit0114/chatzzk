from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import numpy as np
import pytest

from chatzzk.packages.clients._http.client import BaseHttpClient
from chatzzk.packages.clients.ml.asr.asr_http_client import ASRHttpClient
from chatzzk.packages.clients.ml.asr.whisperx_client import WhisperxClient
from chatzzk.packages.clients.ml.exceptions import ASRError
from chatzzk.packages.schemas.config.ml import ASRHttpConfig, WhisperXConfig


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """`BaseHttpClient`의 AsyncMock 객체를 생성합니다."""
    return AsyncMock(spec=BaseHttpClient)


@pytest.fixture
def asr_http_config() -> ASRHttpConfig:
    """테스트용 `ASRHttpConfig` 객체를 생성합니다."""
    return ASRHttpConfig(asr_inference_server_url="http://mock-asr-server:8000")


@pytest.fixture
def whisperx_config() -> WhisperXConfig:
    """
    테스트용 `WhisperXConfig` 객체를 생성합니다.
    실제 모델을 로드하지 않으므로, 설정값은 유효한 형태이기만 하면 됩니다.
    """
    return WhisperXConfig(asr_implementation="whisperx", model_size="tiny", device="cpu", compute_type="int8")


# --- ASRHttpClient Tests ---


class TestASRHttpClient:
    @pytest.mark.asyncio
    async def test_transcribe_success(self, asr_http_config, mock_http_client):
        """
        목적: transcribe 메소드가 성공적으로 HTTP POST 요청을 보내고, 응답을 파싱하여 텍스트를 반환하는지 테스트합니다.
        검증: BaseHttpClient.post가 호출되고, 반환된 텍스트가 예상과 일치하는지 확인합니다.
        """
        # 응답 모킹: ASRResponse Pydantic 모델에 맞는 dict 형태
        mock_http_client.post.return_value = {"text": "hello world"}
        client = ASRHttpClient(config=asr_http_config, http_client=mock_http_client)
        audio_chunk = np.random.rand(16000).astype(np.float32)

        result = await client.transcribe(audio_chunk)

        assert result == "hello world"
        mock_http_client.post.assert_awaited_once()
        # FormData 객체가 data 인자로 전달되었는지 확인
        call_args = mock_http_client.post.call_args
        assert isinstance(call_args.kwargs["data"], aiohttp.FormData)

    @pytest.mark.asyncio
    async def test_transcribe_http_error_raises_asr_error(self, asr_http_config, mock_http_client):
        """
        목적: HTTP 통신 중 오류가 발생했을 때, ASRError 예외가 발생하는지 테스트합니다.
        검증: aiohttp.ClientError가 발생하면, 이를 감싸서 ASRError를 raise하는지 확인합니다.
        """
        mock_http_client.post.side_effect = aiohttp.ClientError("Connection failed")
        client = ASRHttpClient(config=asr_http_config, http_client=mock_http_client)
        audio_chunk = np.random.rand(16000).astype(np.float32)

        with pytest.raises(ASRError) as excinfo:
            await client.transcribe(audio_chunk)

        # 원래 예외(ClientError)가 체인으로 연결되어 있는지 확인
        assert isinstance(excinfo.value.__cause__, aiohttp.ClientError)


# --- WhisperxClient Tests ---


class TestWhisperxClient:
    @patch("chatzzk.packages.clients.ml.asr.whisperx_client.whisperx.load_model")
    def test_initialization_success(self, mock_load_model, whisperx_config):
        """
        목적: WhisperxClient 초기화 시, whisperx.load_model이 올바른 인자로 호출되는지 테스트합니다.
        검증: 실제 모델을 로드하는 대신, mock 객체가 설정값에 맞춰 호출되었는지 확인합니다.
        """
        WhisperxClient(config=whisperx_config, model_path="/models")

        mock_load_model.assert_called_once_with(
            whisperx_config.model_size,
            device=whisperx_config.device,
            compute_type=whisperx_config.compute_type,
            download_root=Path("/models"),
        )

    @patch("chatzzk.packages.clients.ml.asr.whisperx_client.whisperx.load_model")
    def test_initialization_failure_raises_asr_error(self, mock_load_model, whisperx_config):
        """
        목적: 모델 로딩 중 예외가 발생하면, ASRError가 발생하는지 테스트합니다.
        """
        mock_load_model.side_effect = Exception("Model file not found")

        with pytest.raises(ASRError):
            WhisperxClient(config=whisperx_config, model_path="/models")

    @pytest.mark.asyncio
    @patch("chatzzk.packages.clients.ml.asr.whisperx_client.whisperx.load_model")
    async def test_transcribe_success(self, mock_load_model, whisperx_config):
        """
        목적: transcribe 메소드가 내부 모델을 호출하고, 결과를 올바르게 후처리하는지 테스트합니다.
        검증: asyncio.to_thread가 사용되어 블로킹 호출이 이루어지고, 결과 텍스트가 정상적으로 조합되는지 확인합니다.
        """
        # mock 모델의 transcribe 메소드가 반환할 결과 설정
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = {
            "segments": [{"text": "  hello "}, {"text": "world  "}, {"text": ""}],
            "language": "en",
        }
        mock_load_model.return_value = mock_model_instance

        client = WhisperxClient(config=whisperx_config, model_path="/models")
        audio_chunk = np.random.rand(16000).astype(np.float32)

        result = await client.transcribe(audio_chunk)

        # 후처리가 올바르게 되었는지 확인 (양쪽 공백 제거, 빈 문자열 제외)
        assert result == "hello world"
        mock_model_instance.transcribe.assert_called_once()

    @pytest.mark.asyncio
    @patch("chatzzk.packages.clients.ml.asr.whisperx_client.whisperx.load_model")
    async def test_transcribe_failure_raises_asr_error(self, mock_load_model, whisperx_config):
        """
        목적: 모델 추론 중 예외가 발생하면, ASRError가 발생하는지 테스트합니다.
        """
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.side_effect = Exception("CUDA out of memory")
        mock_load_model.return_value = mock_model_instance

        client = WhisperxClient(config=whisperx_config, model_path="/models")
        audio_chunk = np.random.rand(16000).astype(np.float32)

        with pytest.raises(ASRError):
            await client.transcribe(audio_chunk)
