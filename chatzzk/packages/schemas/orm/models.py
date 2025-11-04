from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chatzzk.packages.constants.service_codes import DBDefaults, PlatformCode, ResultObjectFileType, VODProcessStatus


class Base(DeclarativeBase):
    pass


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)

    platform_code: Mapped[PlatformCode] = mapped_column(Enum(PlatformCode), unique=True)
    platform_name: Mapped[str] = mapped_column(String(DBDefaults.PLATFORM_NAME_MAX_LEN))
    donation_unit: Mapped[str | None] = mapped_column(String(DBDefaults.DONATION_UNIT_MAX_LEN))

    channels: Mapped[list["Channel"]] = relationship(back_populates="platform")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))

    is_active: Mapped[bool] = mapped_column(Boolean, server_default=DBDefaults.IS_ACTIVE_DEFAULT)
    last_vod_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    platform: Mapped["Platform"] = relationship(back_populates="channels")
    vods: Mapped[list["VOD"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
    channel_llm_metadata: Mapped["ChannelLLMMetadata"] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )
    channel_metadata: Mapped["ChannelMetadata"] = relationship(back_populates="channel", cascade="all, delete-orphan")
    chzzk_channel: Mapped["ChzzkChannel"] = relationship(back_populates="channel", cascade="all, delete-orphan")


class VOD(Base):
    __tablename__ = "vods"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    channel: Mapped["Channel"] = relationship(back_populates="vods")
    result_object_keys: Mapped[list["ResultObjectKey"]] = relationship(
        back_populates="vod", cascade="all, delete-orphan"
    )
    vod_overall_processing_status: Mapped["VODOverallProcessingStatus"] = relationship(
        back_populates="vod", cascade="all, delete-orphan"
    )
    vod_processing_status_detail: Mapped["VODProcessingStatusDetail"] = relationship(
        back_populates="vod", cascade="all, delete-orphan"
    )
    chzzk_vod: Mapped["ChzzkVOD"] = relationship(back_populates="vod", cascade="all, delete-orphan")


class ChannelMetadata(Base):
    __tablename__ = "channel_metadatas"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))

    metadata_description: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="channel_metadata")


class ChannelLLMMetadata(Base):
    __tablename__ = "channel_llm_metadatas"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))

    llm_metadata_description: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="channel_llm_metadata")


class ResultObjectKey(Base):
    __tablename__ = "result_object_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id"))

    file_type: Mapped[ResultObjectFileType] = mapped_column(Enum(ResultObjectFileType))
    object_key: Mapped[str] = mapped_column(String(DBDefaults.OBJECT_KEY_MAX_LEN))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vod: Mapped["VOD"] = relationship(back_populates="result_object_keys")


class VODOverallProcessingStatus(Base):
    __tablename__ = "vod_overall_processing_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id"))

    status: Mapped[VODProcessStatus] = mapped_column(Enum(VODProcessStatus), server_default=VODProcessStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vod: Mapped["VOD"] = relationship(back_populates="vod_overall_processing_status")


class VODProcessingStatusDetail(Base):
    __tablename__ = "vod_processing_status_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id"))

    status_details: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vod: Mapped["VOD"] = relationship(back_populates="vod_processing_status_detail")


class ChzzkChannel(Base):
    __tablename__ = "chzzk_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))

    platform_channel_id: Mapped[str] = mapped_column(String(100), unique=True)
    channel_name: Mapped[str] = mapped_column(String(100))
    verified_mark: Mapped[bool] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped["Channel"] = relationship(back_populates="chzzk_channel")


class ChzzkVOD(Base):
    __tablename__ = "chzzk_vods"

    id: Mapped[int] = mapped_column(primary_key=True)
    vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id"))

    video_no: Mapped[int] = mapped_column(Integer, unique=True)
    video_title: Mapped[str] = mapped_column(String(100))
    duration: Mapped[int] = mapped_column(Integer)
    video_category_value: Mapped[str] = mapped_column(String(100))
    publish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    live_open_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vod: Mapped["VOD"] = relationship(back_populates="chzzk_vod")
    chzzk_vod_chat_analytics: Mapped["ChzzkVODChatAnalytics"] = relationship(
        back_populates="chzzk_vod", cascade="all, delete-orphan"
    )
    chzzk_vod_asr_analytics: Mapped["ChzzkVODASRAnalytics"] = relationship(
        back_populates="chzzk_vod", cascade="all, delete-orphan"
    )


class ChzzkVODChatAnalytics(Base):
    __tablename__ = "chzzk_vod_chat_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    chzzk_vod_id: Mapped[int] = mapped_column(ForeignKey("chzzk_vods.id"))

    total_chat_count: Mapped[int] = mapped_column(Integer)
    chat_os_type_counts: Mapped[dict] = mapped_column(JSONB)
    chat_participant_count: Mapped[int] = mapped_column(Integer)
    chat_participant_chat_counts: Mapped[dict] = mapped_column(JSONB)
    chat_count_by_subscription: Mapped[dict] = mapped_column(JSONB)
    hidden_chat_count: Mapped[int] = mapped_column(Integer)
    avg_chat_count_per_minute: Mapped[float] = mapped_column(Float)
    total_donation_count: Mapped[int] = mapped_column(Integer)
    total_donation_amount: Mapped[float] = mapped_column(Float)
    donor_count: Mapped[int] = mapped_column(Integer)
    anonymous_donation_amount: Mapped[float] = mapped_column(Float)
    anonymous_donation_count: Mapped[int] = mapped_column(Integer)
    avg_donation_amount: Mapped[float] = mapped_column(Float)
    avg_donation_count_per_minute: Mapped[float] = mapped_column(Float)
    mission_stats: Mapped[dict] = mapped_column(JSONB)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chzzk_vod: Mapped["ChzzkVOD"] = relationship(back_populates="chzzk_vod_chat_analytics")


class ChzzkVODASRAnalytics(Base):
    __tablename__ = "chzzk_vod_asr_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    chzzk_vod_id: Mapped[int] = mapped_column(ForeignKey("chzzk_vods.id"))

    total_speech_time_ms: Mapped[int] = mapped_column(BigInteger)
    avg_speech_time_per_minute: Mapped[float] = mapped_column(Float)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chzzk_vod: Mapped["ChzzkVOD"] = relationship(back_populates="chzzk_vod_asr_analytics")
