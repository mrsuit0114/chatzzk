from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.data_access.repositories.platform import PlatformRepository


def test_find_by_code_existing():
    """find_by_code 호출 시, DB에 플랫폼이 존재하면 해당 객체를 반환하는지 테스트"""
    # given: Mock 세션과 세션 팩토리 설정
    mock_platform = SimpleNamespace(id=123)
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_platform

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__enter__.return_value = mock_session

    repo = PlatformRepository(db_session_factory=mock_session_factory)

    # when: 메서드 호출
    result = repo.find_by_code(PlatformCode.CHZZK)

    # then: Mock 객체가 반환하도록 설정한 값이 나왔는지 확인
    assert result == mock_platform
    mock_session.query.return_value.filter_by.assert_called_once_with(platform_code=PlatformCode.CHZZK)


def test_create():
    """create 호출 시, 올바른 데이터로 ORM 객체를 생성하고 DB에 추가하는지 테스트"""
    # patch를 사용하여 PlatformORM의 생성을 감시
    with patch("chatzzk.packages.data_access.repositories.platform.PlatformORM") as mock_platform_orm:
        # given
        mock_session = MagicMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        repo = PlatformRepository(db_session_factory=mock_session_factory)

        # when
        repo.create(platform_code=PlatformCode.CHZZK, platform_name="치지직", donation_unit="치즈")

        # then
        # 1. PlatformORM 객체가 올바른 인자와 함께 생성되었는가?
        mock_platform_orm.assert_called_once_with(
            platform_code=PlatformCode.CHZZK, platform_name="치지직", donation_unit="치즈"
        )
        # 2. 생성된 객체가 세션에 추가되었는가?
        mock_session.add.assert_called_once()
        # 3. 변경사항이 커밋되었는가?
        mock_session.commit.assert_called_once()
