from types import SimpleNamespace
from unittest.mock import MagicMock

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.services.service_implementations.core.platform_service import PlatformService


def test_add_platform_when_not_existing():
    """플랫폼이 존재하지 않을 때, repository의 create를 호출하는지 테스트"""
    # given: platform_repo를 Mock 객체로 생성
    mock_repo = MagicMock()
    mock_repo.find_by_code.return_value = None  # 존재하지 않는 상황을 가정

    service = PlatformService(platform_repo=mock_repo)

    # when
    service.add_platform(PlatformCode.CHZZK, "치지직", "치즈")

    # then
    # 1. find_by_code가 올바른 인자로 호출되었는가?
    mock_repo.find_by_code.assert_called_once_with(PlatformCode.CHZZK)
    # 2. create가 올바른 인자들로 호출되었는가?
    mock_repo.create.assert_called_once_with(PlatformCode.CHZZK, "치지직", "치즈")


def test_add_platform_when_existing():
    """플랫폼이 이미 존재할 때, repository의 create를 호출하지 않는지 테스트"""
    # given
    mock_platform = SimpleNamespace(id=123)
    mock_repo = MagicMock()
    mock_repo.find_by_code.return_value = mock_platform

    service = PlatformService(platform_repo=mock_repo)

    # when
    result = service.add_platform(PlatformCode.CHZZK, "치지직", "치즈")

    # then
    # 1. find_by_code가 호출되었는가?
    mock_repo.find_by_code.assert_called_once_with(PlatformCode.CHZZK)
    # 2. create는 호출되지 않았는가?
    mock_repo.create.assert_not_called()
    # 3. 기존에 존재하던 객체가 반환되었는가?
    assert result == mock_platform.id
