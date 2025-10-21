from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatzzk.packages.schemas.orm.models import (
    ChannelLlmMetadataORM,
    ChannelORM,
    ChzzkChannelORM,
)
from chatzzk.packages.schemas.repositories.channel import ChzzkChannelCreateDTO


async def get_by_platform_id(session: AsyncSession, platform_channel_id: str) -> ChannelORM | None:
    """
    치지직 플랫폼의 채널 ID를 사용하여 채널 정보를 조회하기 위한 쿼리문을 반환합니다.
    """
    stmt = (
        select(ChannelORM)
        .join(ChzzkChannelORM, ChannelORM.id == ChzzkChannelORM.channel_id)
        .where(ChzzkChannelORM.platform_channel_id == platform_channel_id)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


def create_channel(platform_id: int, dto: ChzzkChannelCreateDTO) -> ChannelORM:
    """
    치지직 채널 생성을 위한 상세 로직.
    필요한 모든 ORM 객체를 생성하고 관계를 설정하여 반환합니다.
    """
    generic_channel = ChannelORM(platform_id=platform_id)
    chzzk_channel = ChzzkChannelORM(channel=generic_channel, **dto.model_dump())
    llm_metadata = ChannelLlmMetadataORM(channel=generic_channel)

    return generic_channel, chzzk_channel, llm_metadata


# def get_discoverable_channels_for_platform(session: Session, offset: int = 0, limit: int = 100) -> list[ChannelORM]:
#     stmt = (
#         select(ChannelORM)
#         .join(ChannelORM.setting)
#         .join(ChannelORM.platform)  # PlatformORM과 조인하여 플랫폼 코드로 필터링
#         .filter(ChannelSettingORM.allow_data_collection)
#         .filter(PlatformORM.platform_code == PlatformCode.CHZZK)  # 치지직 플랫폼 채널만 필터링
#         .order_by(nullsfirst(ChannelSettingORM.last_vod_crawled_at.asc()))
#         .options(
#             joinedload(ChannelORM.platform),
#             joinedload(ChannelORM.chzzk_channel),
#             joinedload(ChannelORM.setting),
#         )
#         .offset(offset)
#         .limit(limit)
#     )
#     return session.scalars(stmt).all()


# def update(session: Session, channel: ChannelORM, **kwargs) -> ChannelORM:
#     """
#     치지직 채널의 상세 정보를 업데이트합니다.
#     """
#     chzzk_channel = channel.chzzk_channel
#     if not chzzk_channel:
#         raise ValueError(f"ChzzkChannelORM not found for ChannelORM ID: {channel.id}")

#     # kwargs에 제공된 필드를 업데이트합니다.
#     if "channel_name" in kwargs:
#         chzzk_channel.channel_name = kwargs["channel_name"]
#     if "is_verified" in kwargs:
#         chzzk_channel.is_verified = kwargs["is_verified"]
#     # 필요한 경우 여기에 다른 chzzk-specific 필드 업데이트 로직을 추가합니다.

#     session.add(chzzk_channel)  # 변경 사항을 세션에 반영
#     session.flush()  # 변경 사항이 DB에 반영되도록 플러시 (아직 커밋은 아님)

#     return channel  # 업데이트된 chzzk_channel을 포함하는 제네릭 채널 반환
