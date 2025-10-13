from sqlalchemy.orm import Session, joinedload

from chatzzk.packages.schemas.orm.models import (
    ChannelLlmMetadataORM,
    ChannelORM,
    ChannelSettingORM,
    ChzzkChannelORM,
    PlatformORM,
)


def get_by_platform_id(session: Session, platform_channel_id: str) -> ChannelORM | None:
    """
    치지직 플랫폼의 채널 ID를 사용하여 채널 정보를 조회합니다.
    """
    query = (
        session.query(ChannelORM)
        .options(
            joinedload(ChannelORM.platform),
            joinedload(ChannelORM.setting),
            joinedload(ChannelORM.chzzk_channel),
        )
        .join(ChannelORM.chzzk_channel)
        .filter(ChzzkChannelORM.channel_id == platform_channel_id)
    )
    return query.first()


def create(session: Session, platform: PlatformORM, **kwargs) -> ChannelORM:
    """
    치지직 채널 생성을 위한 상세 로직.
    필요한 모든 ORM 객체를 생성하고 관계를 설정하여 반환합니다.
    """
    chzzk_channel_id = kwargs.get("chzzk_channel_id")
    channel_name = kwargs.get("channel_name")
    is_verified = kwargs.get("is_verified", False)

    if not all([chzzk_channel_id, channel_name]):
        raise ValueError("chzzk_channel_id and channel_name are required for chzzk channel")

    # 1. 제네릭 및 상세 정보 객체들을 메모리에 생성
    generic_channel = ChannelORM(platform_id=platform.id)
    chzzk_channel = ChzzkChannelORM(
        channel_id=chzzk_channel_id,
        channel_name=channel_name,
        is_verified=is_verified,
    )
    setting = ChannelSettingORM()  # 기본값 사용
    llm_metadata = ChannelLlmMetadataORM(metadata_description={})  # 비어있는 JSON으로 초기화

    # 2. ORM 객체 간의 관계를 메모리에서 연결 (객체 그래프 구성)
    chzzk_channel.channel = generic_channel
    setting.channel = generic_channel
    llm_metadata.channel = generic_channel

    # 3. 최상위 객체를 세션에 추가. cascade 설정에 따라 연관 객체들도 함께 추가됨.
    session.add(generic_channel)

    return generic_channel
