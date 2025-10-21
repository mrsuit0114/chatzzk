from chatzzk.packages.data_access.repositories.chzzk_channel_logic import create_channel
from chatzzk.packages.schemas.orm.models import (
    ChannelLlmMetadataORM,
    ChannelORM,
    ChzzkChannelORM,
)
from chatzzk.packages.schemas.repositories.channel import ChzzkChannelCreateDTO


def test_create_channel_returns_correct_orm_tuple():
    """
    create_channel 호출 시, 반환된 튜플에 ChannelORM, ChzzkChannelORM,
    ChannelLlmMetadataORM 인스턴스가 올바르게 포함되어 있는지 테스트합니다.
    """
    # given
    platform_id = 1
    dto = ChzzkChannelCreateDTO(
        platform_channel_id="test_chzzk_id",
        channel_name="테스트 채널",
        is_verified=False,
    )

    # when
    result_tuple = create_channel(platform_id, dto)

    # then
    assert isinstance(result_tuple, tuple)
    assert len(result_tuple) == 3
    assert isinstance(result_tuple[0], ChannelORM)
    assert isinstance(result_tuple[1], ChzzkChannelORM)
    assert isinstance(result_tuple[2], ChannelLlmMetadataORM)


def test_create_channel_sets_relationships_correctly():
    """
    create_channel 호출 시, 반환된 ORM 객체들 간의 관계가
    올바르게 설정되었는지 테스트합니다.
    """
    # given
    platform_id = 1
    dto = ChzzkChannelCreateDTO(
        platform_channel_id="test_chzzk_id",
        channel_name="테스트 채널",
        is_verified=False,
    )

    # when
    generic_channel, chzzk_channel, llm_metadata = create_channel(platform_id, dto)

    # then
    # 1. ChzzkChannelORM -> ChannelORM 관계가 설정되었는지 확인
    assert chzzk_channel.channel is generic_channel
    # 2. ChannelLlmMetadataORM -> ChannelORM 관계가 설정되었는지 확인
    assert llm_metadata.channel is generic_channel
    # 3. DTO의 값이 ChzzkChannelORM에 잘 채워졌는지 확인
    assert chzzk_channel.platform_channel_id == dto.platform_channel_id
    assert chzzk_channel.channel_name == dto.channel_name
