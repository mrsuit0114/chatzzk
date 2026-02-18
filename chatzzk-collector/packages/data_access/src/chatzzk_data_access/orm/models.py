from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chatzzk_core.constants import PlatformCode, UserRole, VODPipelineStatus


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # [필수] Supabase가 발급한 유저의 UUID를 저장할 컬럼
    supabase_uid: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True)
    user_name: Mapped[str] = mapped_column(Text, unique=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owned_channel: Mapped["Channel"] = relationship(
        "Channel", back_populates="owner", foreign_keys="[Channel.user_id]", uselist=False
    )
    editor_channel: Mapped["Channel"] = relationship(
        "Channel", back_populates="editor", foreign_keys="[Channel.editor_id]", uselist=False
    )

    __table_args__ = (
        CheckConstraint(
            "char_length(user_name) >= 4 AND char_length(user_name) <= 20 AND user_name ~ '^[a-z0-9]+$'",
            name="check_user_name_format",
        ),
    )


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    platform_code: Mapped[PlatformCode] = mapped_column(Enum(PlatformCode), unique=True)
    platform_url: Mapped[str] = mapped_column(Text)
    platform_name: Mapped[str] = mapped_column(Text)
    donation_unit: Mapped[str | None] = mapped_column(Text)
    platform_features: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))

    channels: Mapped[list["Channel"]] = relationship(back_populates="platform")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", name="channels_user_id_fkey"), unique=True)
    editor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", name="channels_editor_id_fkey"), unique=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))

    platform_channel_id: Mapped[str] = mapped_column(Text, index=True)
    channel_name: Mapped[str] = mapped_column(Text, index=True)
    last_vod_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_collection_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    vod_exposure_delay_hours: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    vod_detail_exposure_delay_hours: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("platform_id", "platform_channel_id", name="uq_channel_platform_identifier"),)

    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="owned_channel",
    )
    editor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[editor_id],
        back_populates="editor_channel",
    )
    platform: Mapped["Platform"] = relationship(back_populates="channels")
    vods: Mapped[list["VOD"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
    channel_metadata: Mapped["ChannelMetadata"] = relationship(
        back_populates="channel", cascade="all, delete-orphan", uselist=False
    )


class VOD(Base):
    __tablename__ = "vods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE", name="vods_channel_id_fkey"))

    video_no: Mapped[str] = mapped_column(Text, index=True)
    video_title: Mapped[str] = mapped_column(Text)
    duration: Mapped[int] = mapped_column(Integer)
    publish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pipeline_status: Mapped[VODPipelineStatus] = mapped_column(
        Enum(VODPipelineStatus), server_default=text(f"'{VODPipelineStatus.PENDING.value}'")
    )
    is_exposed: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("channel_id", "video_no", name="uq_vod_channel_video"),
        Index("idx_vod_status_created", "pipeline_status", "publish_date"),
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE", name="channel_metadata_channel_id_fkey"), unique=True
    )

    attributes: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), server_default=text("'{}'::jsonb"))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="channel_metadata")
