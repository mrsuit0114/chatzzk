# tests/packages/schemas/config/test_configs.py

import pytest
from pydantic import TypeAdapter, ValidationError

from chatzzk.packages.constants.service_codes import MIN_SILENCE_DURATION_MS
from chatzzk.packages.schemas.config.api import ApiClientConfig, BaseHttpConfig, ChzzkApiConfig
from chatzzk.packages.schemas.config.database import DatabaseConfig, PostgresConfig
from chatzzk.packages.schemas.config.ml import ASRConfig, ASRHttpConfig, WhisperXConfig
from chatzzk.packages.schemas.config.settings import Settings
from chatzzk.packages.schemas.config.storage import MinioConfig


def test_database_config_success():
    """
    목적: 유효한 DB 설정값이 주어졌을 때, PostgresConfig 모델로 성공적으로 파싱되는지 테스트합니다.
    이유: 애플리케이션의 가장 기본적인 데이터베이스 연결 설정이 올바르게 로드되는지 보장하기 위함입니다.
    """
    config_data = {
        "db_implementation": "postgres",
        "database_url": "postgresql://user:pass@host:5432/db",
    }
    db_config = TypeAdapter(DatabaseConfig).validate_python(config_data)
    assert isinstance(db_config, PostgresConfig)
    assert db_config.database_url == "postgresql://user:pass@host:5432/db"


def test_database_config_missing_field():
    """
    목적: 필수 필드(database_url)가 누락되었을 때 ValidationError가 발생하는지 테스트합니다.
    이유: 불완전한 설정으로 애플리케이션이 실행되는 것을 방지하는 유효성 검사 기능이 잘 동작하는지 확인합니다.
    """
    invalid_data = {"db_implementation": "postgres"}
    with pytest.raises(ValidationError):
        TypeAdapter(DatabaseConfig).validate_python(invalid_data)


def test_asr_config_discriminator():
    """
    목적: ASRConfig의 discriminator 필드('asr_implementation') 값에 따라 올바른 하위 모델로 파싱되는지 테스트합니다.
    이유: 런타임에 어떤 ASR 클라이언트 구현체를 주입할지 결정하는 핵심 로직이 정확하게 동작하는지 보장하기 위함입니다.
    """
    adapter = TypeAdapter(ASRConfig)
    # 1. "whisperx" 구현체 테스트
    whisperx_data = {
        "asr_implementation": "whisperx",
        "model_size": "large-v3",
        "device": "cuda",
    }
    asr_config_1 = adapter.validate_python(whisperx_data)
    assert isinstance(asr_config_1, WhisperXConfig)
    assert asr_config_1.model_size == "large-v3"

    # 2. "http" 구현체 테스트
    http_data = {
        "asr_implementation": "http",
        "asr_inference_server_url": "http://localhost:8000",
    }
    asr_config_2 = adapter.validate_python(http_data)
    assert isinstance(asr_config_2, ASRHttpConfig)
    assert asr_config_2.asr_inference_server_url == "http://localhost:8000"

    # 3. 유효하지 않은 구현체 테스트
    invalid_data = {"asr_implementation": "invalid_one"}
    with pytest.raises(ValidationError):
        adapter.validate_python(invalid_data)


def test_api_client_config_success():
    """
    목적: ApiClientConfig가 새로운 계층 구조(BaseHttpConfig)에 따라 올바르게 파싱되는지 테스트합니다.
    이유: 설정 리팩토링 이후에도 HTTP 클라이언트의 재시도, Rate Limit 등의 핵심 동작이
          올바르게 설정되는지 보장하기 위함입니다.
    """
    # 1. 모든 값을 명시적으로 제공
    config_data_1 = {
        "base_http": {
            "retry": {"attempts": 5, "wait_min_s": 1, "wait_max_s": 5},
            "rate_limit": {"max_rate": 10, "time_period": 2},
            "default_headers": {"User-Agent": "test-agent"},
        },
        "chzzk_api": {
            "channel_info_template": "mock_channel_info",
            "channel_vods_info_template": "mock_channel_vods",
            "vod_info_template": "mock_vod_info",
            "vod_chats_template": "mock_vod_chats",
            "vod_url_template": "mock_vod_url",
            "https_proxy": "https://test.proxy",
            "vod_manifest_headers": {"Accept": "application/x-mpegURL"},
            "dash_ns": {"mpd": "urn:test:dash"},
        },
    }
    api_config_1 = ApiClientConfig.model_validate(config_data_1)
    assert api_config_1.base_http.retry.attempts == 5
    assert api_config_1.base_http.rate_limit.max_rate == 10
    assert api_config_1.base_http.default_headers["User-Agent"] == "test-agent"
    assert api_config_1.chzzk_api.https_proxy == "https://test.proxy"

    # 2. 일부 값만 제공 (나머지는 기본값 사용)
    config_data_2 = {
        "base_http": {"retry": {"attempts": 1}},
        "chzzk_api": {
            "channel_info_template": "mock_channel_info_2",
            "channel_vods_info_template": "mock_channel_vods_2",
            "vod_info_template": "mock_vod_info_2",
            "vod_chats_template": "mock_vod_chats_2",
            "vod_url_template": "mock_vod_url_2",
        },
    }
    api_config_2 = ApiClientConfig.model_validate(config_data_2)
    assert api_config_2.base_http.retry.attempts == 1
    assert api_config_2.base_http.retry.wait_max_s == 2  # 기본값
    assert api_config_2.base_http.rate_limit.max_rate == 5  # 기본값
    assert api_config_2.chzzk_api.https_proxy is None  # 기본값

    # 3. chzzk_api의 필수 값만 제공 (base_http는 전체 기본값 사용)
    config_data_3 = {
        "chzzk_api": {
            "channel_info_template": "mock_channel_info_2",
            "channel_vods_info_template": "mock_channel_vods_2",
            "vod_info_template": "mock_vod_info_2",
            "vod_chats_template": "mock_vod_chats_2",
            "vod_url_template": "mock_vod_url_2",
        }
    }
    api_config_3 = ApiClientConfig.model_validate(config_data_3)
    assert isinstance(api_config_3.base_http, BaseHttpConfig)
    assert api_config_3.base_http.retry.attempts == 3  # 기본값
    assert api_config_3.base_http.rate_limit.max_rate == 5  # 기본값


def test_top_level_settings_composition():
    """
    목적: 최상위 Settings 모델이 리팩토링된 ApiClientConfig를 포함하여 올바르게 구성되는지 테스트합니다.
    이유: 애플리케이션 전체 설정의 단일 진입점(Settings)이 계층적으로 잘 정의되었는지,
          특히 `api.base_http` 경로를 통해 설정 값에 접근할 수 있는지 확인하기 위함입니다.
    """
    full_config_data = {
        "db": {
            "db_implementation": "postgres",
            "database_url": "postgresql://user:pass@host:5432/db",
        },
        "storage": {
            "storage_implementation": "minio",
            "endpoint": "localhost:9000",
            "access_key": "minio",
            "secret_key": "minio123",
            "bucket_name": "test",
        },
        "asr": {
            "asr_implementation": "whisperx",
            "model_size": "large-v3",
        },
        "vad": {
            "vad_implementation": "silero",
            "min_silence_duration_ms": 500,
        },
        "api": {
            "base_http": {
                "retry": {"attempts": 3},
                "rate_limit": {"max_rate": 10, "time_period": 1},
                "default_headers": {"User-Agent": "test-agent-settings"},
            },
            "chzzk_api": {
                "channel_info_template": "mock_channel_info_settings",
                "channel_vods_info_template": "mock_channel_vods_settings",
                "vod_info_template": "mock_vod_info_settings",
                "vod_chats_template": "mock_vod_chats_settings",
                "vod_url_template": "mock_vod_url_settings",
                "https_proxy": "https://test.proxy.settings",
                "vod_manifest_headers": {"Accept-Language": "ko-KR"},
                "dash_ns": {"mpd": "urn:test:dash:settings"},
            },
        },
    }
    settings = Settings.model_validate(full_config_data)

    assert isinstance(settings.db, PostgresConfig)
    assert isinstance(settings.storage, MinioConfig)
    assert isinstance(settings.asr, WhisperXConfig)
    assert isinstance(settings.api, ApiClientConfig)
    assert isinstance(settings.api.chzzk_api, ChzzkApiConfig)
    # 필드 값 체크
    assert settings.vad.min_silence_duration_ms == MIN_SILENCE_DURATION_MS
    assert settings.db.database_url == "postgresql://user:pass@host:5432/db"
    assert settings.api.base_http.retry.attempts == 3
    assert settings.api.base_http.rate_limit.max_rate == 10
    assert settings.api.chzzk_api.https_proxy == "https://test.proxy.settings"
