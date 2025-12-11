from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, func, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chatzzk_constants.service_codes import DBDefault, PlatformCode, VODProcessingStatus


class Base(DeclarativeBase):
    pass


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
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))

    platform_channel_id: Mapped[str] = mapped_column(String(DBDefault.Len.ID))
    channel_name: Mapped[str] = mapped_column(String(DBDefault.Len.NAME))
    channel_url: Mapped[str] = mapped_column(String(DBDefault.Len.URL), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=DBDefault.IS_ACTIVE)
    last_vod_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("platform_id", "platform_channel_id", name="uq_channel_platform_identifier"),)

    platform: Mapped["Platform"] = relationship(back_populates="channels")
    vods: Mapped[list["VOD"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
    channel_llm_context: Mapped["ChannelLLMContext"] = relationship(
        back_populates="channel", cascade="all, delete-orphan", uselist=False
    )
    chzzk_channel: Mapped["ChzzkChannel | None"] = relationship(
        back_populates="channel", cascade="all, delete-orphan", uselist=False
    )


class VOD(Base):
    __tablename__ = "vods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE", name="vods_channel_id_fkey"))

    video_no: Mapped[str] = mapped_column(String(DBDefault.Len.ID))
    video_title: Mapped[str] = mapped_column(String(DBDefault.Len.NAME))
    duration: Mapped[int] = mapped_column(Integer)
    publish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vod_url: Mapped[str] = mapped_column(String(DBDefault.Len.URL))
    detail_chunk_count: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("channel_id", "video_no", name="uq_vod_channel_video"),)

    channel: Mapped["Channel"] = relationship(back_populates="vods")
    vod_processing_status: Mapped["VODProcessingStatus"] = relationship(
        back_populates="vod", cascade="all, delete-orphan", uselist=False
    )


class ChannelLLMContext(Base):
    __tablename__ = "channel_llm_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE", name="channel_llm_contexts_channel_id_fkey"), unique=True
    )

    llm_context: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), server_default=text("'{}'::jsonb"))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="channel_llm_context")


class VODProcessingStatus(Base):
    __tablename__ = "vod_processing_statuses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vod_id: Mapped[int] = mapped_column(
        ForeignKey("vods.id", ondelete="CASCADE", name="vod_processing_statuses_vod_id_fkey"), unique=True
    )

    status: Mapped[VODProcessingStatus] = mapped_column(
        Enum(VODProcessingStatus), server_default=text(f"'{DBDefault.VOD_PROCESSING_STATUS}'")
    )
    status_details: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), server_default=text("'{}'::jsonb"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vod: Mapped["VOD"] = relationship(back_populates="vod_processing_status")


class ChzzkChannel(Base):
    __tablename__ = "chzzk_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE", name="chzzk_channels_channel_id_fkey"), unique=True
    )

    verified_mark: Mapped[bool] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="chzzk_channel")


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
