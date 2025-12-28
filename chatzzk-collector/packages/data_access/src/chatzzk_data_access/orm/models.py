from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chatzzk_core.constants import DBDefault, PlatformCode, VODPipelineStatus


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # [필수] Supabase가 발급한 유저의 UUID를 저장할 컬럼
    # 웹 서비스에서 로그인 성공 시, 이 값을 기준으로 우리 DB의 유저를 찾습니다.
    supabase_uid: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, index=True)

    email: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    channels: Mapped[list["Channel"]] = relationship(back_populates="owner")


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)

    platform_code: Mapped[PlatformCode] = mapped_column(Enum(PlatformCode), unique=True)
    platform_url: Mapped[str] = mapped_column(String(DBDefault.Len.URL))
    platform_name: Mapped[str] = mapped_column(String(DBDefault.Len.NAME))
    donation_unit: Mapped[str | None] = mapped_column(String(DBDefault.Len.NAME))

    channels: Mapped[list["Channel"]] = relationship(back_populates="platform")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", name="channels_user_id_fkey"))
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))

    platform_channel_id: Mapped[str] = mapped_column(String(DBDefault.Len.ID), index=True)
    channel_name: Mapped[str] = mapped_column(String(DBDefault.Len.NAME))
    last_vod_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_collection_enabled: Mapped[bool] = mapped_column(Boolean, server_default=DBDefault.IS_COLLECTION_ENABLED)
    vod_exposure_delay_hours: Mapped[int] = mapped_column(
        Integer, server_default=text(f"{DBDefault.VOD_EXPOSURE_DELAY_HOURS}")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("platform_id", "platform_channel_id", name="uq_channel_platform_identifier"),)

    owner: Mapped["User"] = relationship(back_populates="channels")
    platform: Mapped["Platform"] = relationship(back_populates="channels")
    vods: Mapped[list["VOD"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
    channel_metadata: Mapped["ChannelMetadata"] = relationship(
        back_populates="channel", cascade="all, delete-orphan", uselist=False
    )


class VOD(Base):
    __tablename__ = "vods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE", name="vods_channel_id_fkey"))

    video_no: Mapped[str] = mapped_column(String(DBDefault.Len.ID), index=True)
    video_title: Mapped[str] = mapped_column(String(DBDefault.Len.NAME))
    duration: Mapped[int] = mapped_column(Integer)
    publish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pipeline_status: Mapped[VODPipelineStatus] = mapped_column(
        Enum(VODPipelineStatus), server_default=text(f"'{DBDefault.VOD_PIPELINE_STATUS}'")
    )
    is_exposed: Mapped[bool] = mapped_column(Boolean, server_default=DBDefault.IS_EXPOSED)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("channel_id", "video_no", name="uq_vod_channel_video"),
        Index("idx_vod_status_created", "pipeline_status", "created_at"),
        Index("idx_vod_exposed_publish", "is_exposed", "publish_date"),
    )

    channel: Mapped["Channel"] = relationship(back_populates="vods")
    pipeline_log: Mapped["VODPipelineLog"] = relationship(
        back_populates="vod", cascade="all, delete-orphan", uselist=False
    )


class VODPipelineLog(Base):
    __tablename__ = "vod_pipeline_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vod_id: Mapped[int] = mapped_column(
        ForeignKey("vods.id", ondelete="CASCADE", name="vod_pipeline_logs_vod_id_fkey"), unique=True
    )

    process_details: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), server_default=text("'{}'::jsonb"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vod: Mapped["VOD"] = relationship(back_populates="pipeline_log")


class ChannelMetadata(Base):
    __tablename__ = "channel_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE", name="channel_metadata_channel_id_fkey"), unique=True
    )

    attributes: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), server_default=text("'{}'::jsonb"))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="channel_metadata")


# class ChzzkChannel(Base):
#     __tablename__ = "chzzk_channels"

#     id: Mapped[int] = mapped_column(primary_key=True)
#     channel_id: Mapped[int] = mapped_column(
#         ForeignKey("channels.id", ondelete="CASCADE", name="chzzk_channels_channel_id_fkey"), unique=True
#     )

#     verified_mark: Mapped[bool] = mapped_column(Boolean)

#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
#     )

#     channel: Mapped["Channel"] = relationship(back_populates="chzzk_channel")


# class ChzzkVODAnalysis(Base):
#     __tablename__ = "chzzk_vod_analyses"

#     id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
#     vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id", ondelete="CASCADE", name="chzzk_vod_analyses_vod_id_fkey"))

#     total_chat_count: Mapped[int] = mapped_column(Integer)
#     chat_os_type_counts: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB))
#     chat_participant_count: Mapped[int] = mapped_column(Integer)
#     chat_participant_chat_counts: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB))
#     chat_count_by_subscription: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB))
#     hidden_chat_count: Mapped[int] = mapped_column(Integer)
#     avg_chat_count_per_minute: Mapped[float] = mapped_column(Float)
#     total_donation_count: Mapped[int] = mapped_column(Integer)
#     total_donation_amount: Mapped[float] = mapped_column(Float)
#     donor_count: Mapped[int] = mapped_column(Integer)
#     anonymous_donation_amount: Mapped[float] = mapped_column(Float)
#     anonymous_donation_count: Mapped[int] = mapped_column(Integer)
#     avg_donation_amount: Mapped[float] = mapped_column(Float)
#     avg_donation_count_per_minute: Mapped[float] = mapped_column(Float)
#     mission_stats: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB))

#     total_speech_time_ms: Mapped[int] = mapped_column(BigInteger)
#     avg_speech_time_per_minute: Mapped[float] = mapped_column(Float)
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
#     )
