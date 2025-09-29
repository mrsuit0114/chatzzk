# tests/packages/schemas/config/test_configs.py

import pytest
from pydantic import TypeAdapter, ValidationError

from chatzzk.packages.constants.service_codes import MIN_SILENCE_DURATION_MS
from chatzzk.packages.schemas.config.api import ApiClientConfig
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
    # DatabaseConfig는 Union 타입이므로, model_validate를 통해 파싱합니다.
    db_config = DatabaseConfig.model_validate(config_data)
    assert (
        type(db_config) is PostgresConfig
    )  # Pydantic v2에서 Annotated는 subscripted generic으로 취급되기 때문에, 파이썬 isinstance/issubclass 체크에서 바로 사용할 수 없습니다.
    assert db_config.database_url == "postgresql://user:pass@host:5432/db"


def test_database_config_missing_field():
    """
    목적: 필수 필드(database_url)가 누락되었을 때 ValidationError가 발생하는지 테스트합니다.
    이유: 불완전한 설정으로 애플리케이션이 실행되는 것을 방지하는 유효성 검사 기능이 잘 동작하는지 확인합니다.
    """
    invalid_data = {"db_implementation": "postgres"}
    with pytest.raises(ValidationError):
        DatabaseConfig.model_validate(invalid_data)


def test_asr_config_discriminator():
    """
    목적: ASRConfig의 discriminator 필드('asr_implementation') 값에 따라 올바른 하위 모델로 파싱되는지 테스트합니다.
    이유: 런타임에 어떤 ASR 클라이언트 구현체를 주입할지 결정하는 핵심 로직이 정확하게 동작하는지 보장하기 위함입니다.
    """
    adapter = TypeAdapter(ASRConfig)  # Union타입이므로 model_validate사용 불가 -> parse_obj_as는 deprecated
    # 1. "whisperx" 구현체 테스트
    whisperx_data = {
        "asr_implementation": "whisperx",
        "model_size": "large-v3",
        "device": "cuda",
    }
    asr_config_1 = adapter.validate_python(whisperx_data)
    assert type(asr_config_1) is WhisperXConfig
    assert asr_config_1.model_size == "large-v3"

    # 2. "http" 구현체 테스트
    http_data = {
        "asr_implementation": "http",
        "asr_inference_server_url": "http://localhost:8000",
    }
    asr_config_2 = adapter.validate_python(http_data)
    assert type(asr_config_2) is ASRHttpConfig
    assert asr_config_2.asr_inference_server_url == "http://localhost:8000"

    # 3. 유효하지 않은 구현체 테스트
    invalid_data = {"asr_implementation": "invalid_one"}
    with pytest.raises(ValidationError):
        adapter.validate_python(invalid_data)


def test_api_client_config_success():
    """
    목적: 유효한 API 클라이언트 설정값이 주어졌을 때, ApiClientConfig 모델로 성공적으로 파싱되는지 테스트합니다.
    이유: HTTP 클라이언트의 재시도 및 Rate Limit 같은 핵심 동작이 올바르게 설정되는지 보장하기 위함입니다.
    """
    # 1. 모든 값을 명시적으로 제공
    config_data_1 = {
        "retry": {"attempts": 5, "wait_min_s": 1, "wait_max_s": 5},
        "rate_limit": {"max_rate": 10, "time_period": 2},
    }
    api_config_1 = ApiClientConfig.model_validate(config_data_1)
    assert api_config_1.retry.attempts == 5
    assert api_config_1.rate_limit.max_rate == 10

    # 2. 일부 값만 제공 (나머지는 기본값 사용)
    config_data_2 = {"retry": {"attempts": 1}}
    api_config_2 = ApiClientConfig.model_validate(config_data_2)
    assert api_config_2.retry.attempts == 1
    assert api_config_2.retry.wait_max_s == 2  # 기본값
    assert api_config_2.rate_limit.max_rate == 5  # 기본값

    # 3. 빈 dict 제공 (모두 기본값 사용)
    config_data_3 = {}
    api_config_3 = ApiClientConfig.model_validate(config_data_3)
    assert api_config_3.retry.attempts == 3
    assert api_config_3.rate_limit.max_rate == 5


def test_top_level_settings_composition():
    """
    목적: 최상위 Settings 모델이 여러 하위 설정 모델들을 올바르게 포함하여 구성되는지 테스트합니다.
    이유: 애플리케이션 전체의 설정을 담는 단일 진입점(Settings)이 계층적으로 잘 정의되었는지 확인하기 위함입니다.
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
            "retry": {"attemps": 3},
            "rate_limit": {"max_rate": 10, "time_period": 1},
        },
    }
    adapter = TypeAdapter(Settings)
    settings = adapter.validate_python(full_config_data)

    assert type(settings.db) is PostgresConfig
    assert type(settings.storage) is MinioConfig
    assert type(settings.asr) is WhisperXConfig
    assert type(settings.api) is ApiClientConfig
    # 필드 값 체크
    assert settings.vad.min_silence_duration_ms == MIN_SILENCE_DURATION_MS
    assert settings.db.database_url == "postgresql://user:pass@host:5432/db"
    assert settings.api.retry.attempts == 3
    assert settings.api.rate_limit.max_rate == 10
