# tests/packages/schemas/orm/test_models.py

from chatzzk.packages.schemas.orm.models import StringAsInt


def test_string_as_int_process_bind_param():
    """
    목적: 파이썬의 문자열(str) 값이 DB에 저장될 때 정수(int)로 올바르게 변환되는지 테스트합니다.
    이유: 애플리케이션에서 문자열로 다루는 video_no를 DB에 BigInteger 타입으로 문제없이 저장하기 위함입니다.
    """
    # 준비 (Arrange)
    decorator = StringAsInt()
    dialect = None  # 이 테스트에서는 dialect 객체가 필요 없습니다.

    # 실행 (Act)
    # 1. 문자열 "12345"를 변환합니다.
    result_from_str = decorator.process_bind_param("12345", dialect)

    # 2. None 값을 변환합니다.
    result_from_none = decorator.process_bind_param(None, dialect)

    # 검증 (Assert)
    assert result_from_str == 12345
    assert isinstance(result_from_str, int)
    assert result_from_none is None


def test_string_as_int_process_result_value():
    """
    목적: DB의 정수(int) 값이 파이썬으로 로드될 때 문자열(str)로 올바르게 변환되는지 테스트합니다.
    이유: DB에 BigInteger로 저장된 video_no를 애플리케이션에서 일관되게 문자열 타입으로 사용하기 위함입니다.
    """
    # 준비 (Arrange)
    decorator = StringAsInt()
    dialect = None  # 이 테스트에서는 dialect 객체가 필요 없습니다.

    # 실행 (Act)
    # 1. 정수 12345를 변환합니다.
    result_from_int = decorator.process_result_value(12345, dialect)

    # 2. None 값을 변환합니다.
    result_from_none = decorator.process_result_value(None, dialect)

    # 검증 (Assert)
    assert result_from_int == "12345"
    assert isinstance(result_from_int, str)
    assert result_from_none is None
