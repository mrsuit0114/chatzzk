# tests/packages/utils/test_file_io.py

import io

import pytest
from pydantic import BaseModel

from chatzzk.packages.data_access.serialization import load_jsonl_as_models, load_jsonl_as_models_from_bytes


# 테스트에 사용할 간단한 Pydantic 모델 정의
class SimpleModel(BaseModel):
    id: int
    name: str


def test_load_jsonl_as_models_from_bytes_success():
    """
    목적: 정상적인 JSONL 바이트 데이터를 Pydantic 모델 리스트로 성공적으로 변환하는지 테스트합니다.
    이유: 함수의 가장 기본적인 핵심 기능(Happy Path)이 올바르게 동작하는지 보장하기 위함입니다.
    """
    # 준비 (Arrange): 여러 줄의 유효한 JSONL 형식의 바이트 데이터를 준비합니다.
    jsonl_bytes = b'{"id": 1, "name": "apple"}\n{"id": 2, "name": "banana"}'

    # 실행 (Act): 테스트할 함수를 호출합니다.
    models = load_jsonl_as_models_from_bytes(jsonl_bytes, SimpleModel)

    # 검증 (Assert): 반환된 리스트의 길이와 각 객체의 타입, 내용을 확인합니다.
    assert len(models) == 2
    assert isinstance(models[0], SimpleModel)
    assert models[0].id == 1
    assert models[0].name == "apple"
    assert isinstance(models[1], SimpleModel)
    assert models[1].id == 2
    assert models[1].name == "banana"


def test_load_jsonl_as_models_from_bytes_with_empty_lines():
    """
    목적: 데이터 중간에 빈 줄이나 공백만 있는 줄이 포함되어도 이를 무시하고 정상 처리하는지 테스트합니다.
    이유: 데이터 파일은 예상치 못한 공백을 포함할 수 있으며, 이로 인해 파싱 로직이 실패해서는 안 됩니다.
    """
    # 준비 (Arrange): 빈 줄과 공백 라인이 포함된 데이터를 준비합니다.
    jsonl_bytes = b'\n{"id": 1, "name": "apple"}\n\n   \n\n{"id": 2, "name": "banana"}\n'

    # 실행 (Act): 함수를 호출합니다.
    models = load_jsonl_as_models_from_bytes(jsonl_bytes, SimpleModel)

    # 검증 (Assert): 빈 줄은 무시하고 유효한 데이터만 파싱했는지 확인합니다.
    assert len(models) == 2
    assert models[0].id == 1
    assert models[1].id == 2


@pytest.mark.parametrize(
    "invalid_line",
    [
        b"this is not json",  # JSON 형식이 아님
        b'{"id": 3, "name": "cherry"',  # 닫는 괄호가 없음
        b'{"id": 4, "extra_field": true}',  # 모델에 정의되지 않은 필드 포함
    ],
)
def test_load_jsonl_as_models_from_bytes_skip_invalid_line(invalid_line, caplog):
    """
    목적: 유효하지 않은 JSON 라인이 포함되었을 때, 해당 라인을 건너뛰고 다음 라인을 계속 처리하는지 테스트합니다.
    이유: 일부 데이터가 손상되더라도 전체 파싱 작업이 중단되지 않고, 유효한 데이터는 최대한 복구해야 합니다.
    """
    # 준비 (Arrange): 정상 데이터 사이에 다양한 유형의 비정상 데이터를 삽입합니다.
    jsonl_bytes = b'{"id": 1, "name": "apple"}\n' + invalid_line + b'\n{"id": 2, "name": "banana"}'

    # 실행 (Act): 함수를 호출합니다.
    models = load_jsonl_as_models_from_bytes(jsonl_bytes, SimpleModel)

    # 검증 (Assert)
    # 1. 비정상 라인은 건너뛰고, 정상적인 데이터만 파싱했는지 확인합니다.
    assert len(models) == 2
    assert models[0].id == 1
    assert models[1].id == 2


def test_load_jsonl_as_models_from_empty_bytes():
    """
    목적: 입력 데이터가 비어있을 때, 에러 없이 빈 리스트를 반환하는지 테스트합니다.
    이유: 비어있는 파일이나 데이터는 정상적인 예외 케이스이므로, 안정적으로 처리해야 합니다.
    """
    # 준비, 실행
    models = load_jsonl_as_models_from_bytes(b"", SimpleModel)

    # 검증
    assert models == []


def test_load_jsonl_as_models_with_file_handle():
    """
    목적: 바이트 데이터가 아닌 파일 핸들(File-like object)을 직접 입력받는 경우에도 정상 동작하는지 테스트합니다.
    이유: load_jsonl_as_models_from_bytes의 기반이 되는 핵심 함수이므로, 자체 기능도 검증해야 합니다.
    """
    # 준비
    jsonl_string = '{"id": 1, "name": "apple"}\n{"id": 2, "name": "banana"}'
    file_handle = io.BytesIO(jsonl_string.encode("utf-8"))

    # 실행
    models = load_jsonl_as_models(file_handle, SimpleModel)

    # 검증
    assert len(models) == 2
    assert models[0].id == 1
    assert models[1].name == "banana"
