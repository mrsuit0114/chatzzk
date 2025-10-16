from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from chatzzk.packages.constants.service_codes import PlatformCode, ResultObjectFileType, VodProcessStatus
from chatzzk.packages.data_access.db.base import Base


class StringAsInt(TypeDecorator):
    """
    DB에는 BigInteger로 저장하지만, 파이썬 애플리케이션에서는
    문자열(String)로 다룰 수 있게 해주는 커스텀 타입.
    """

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value, dialect):
        # 파이썬의 값을 DB에 저장할 때: str -> int
        if value is not None:
            return int(value)

    def process_result_value(self, value, dialect):
        # DB의 값을 파이썬으로 읽어올 때: int -> str
        if value is not None:
            return str(value)


class PlatformORM(Base):
    __tablename__ = "platforms"

    id = Column(SmallInteger, primary_key=True)
    platform_code = Column(Enum(PlatformCode), unique=True, nullable=False)
    platform_name = Column(String(100), nullable=False)
    donation_unit = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    channels = relationship("ChannelORM", back_populates="platform")


class ChannelORM(Base):
    __tablename__ = "channels"
    id = Column(BigInteger, primary_key=True)
    platform_id = Column(SmallInteger, ForeignKey("platforms.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    platform = relationship("PlatformORM", back_populates="channels")
    vods = relationship("VodORM", back_populates="channel", cascade="all, delete-orphan")
    setting = relationship("ChannelSettingORM", back_populates="channel", uselist=False, cascade="all, delete-orphan")
    llm_metadata = relationship(
        "ChannelLlmMetadataORM", back_populates="channel", uselist=False, cascade="all, delete-orphan"
    )
    chzzk_channel = relationship(
        "ChzzkChannelORM", back_populates="channel", uselist=False, cascade="all, delete-orphan"
    )


class VodORM(Base):
    __tablename__ = "vods"
    id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    channel = relationship("ChannelORM", back_populates="vods")
    result_object_keys = relationship("ResultObjectKeyORM", back_populates="vod", cascade="all, delete-orphan")
    processing_status = relationship(
        "VodProcessingStatusORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )
    processing_history = relationship(
        "VodProcessingHistoryORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )
    chzzk_vod = relationship("ChzzkVodORM", back_populates="vod", uselist=False, cascade="all, delete-orphan")


class ChannelSettingORM(Base):
    __tablename__ = "channel_settings"

    id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), unique=True, nullable=False)

    allow_data_collection = Column(Boolean, nullable=False, default=False)
    is_exposure_default = Column(Boolean, nullable=False, default=True)
    allow_detailed_stats = Column(Boolean, nullable=False, default=False)
    last_vod_crawled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    channel = relationship("ChannelORM", back_populates="setting")


class ChannelLlmMetadataORM(Base):
    __tablename__ = "channel_llm_metadatas"

    id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), unique=True, nullable=False)

    metadata_description = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    channel = relationship("ChannelORM", back_populates="llm_metadata")


class ResultObjectKeyORM(Base):
    __tablename__ = "result_object_keys"
    __table_args__ = (UniqueConstraint("vod_id", "file_type", name="uq_vod_id_file_type"),)

    id = Column(BigInteger, primary_key=True)
    vod_id = Column(BigInteger, ForeignKey("vods.id", ondelete="CASCADE"), nullable=False)

    file_type = Column(Enum(ResultObjectFileType), nullable=False)
    object_key = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vod = relationship("VodORM", back_populates="result_object_keys")


class VodProcessingStatusORM(Base):
    __tablename__ = "vod_processing_statuses"

    id = Column(BigInteger, primary_key=True)
    vod_id = Column(BigInteger, ForeignKey("vods.id", ondelete="CASCADE"), unique=True, nullable=False)

    status = Column(Enum(VodProcessStatus), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vod = relationship("VodORM", back_populates="processing_status")


class VodProcessingHistoryORM(Base):
    __tablename__ = "vod_processing_histories"

    id = Column(BigInteger, primary_key=True)
    vod_id = Column(BigInteger, ForeignKey("vods.id", ondelete="CASCADE"), unique=True, nullable=False)

    status_details = Column(JSONB, nullable=False)
    fail_count = Column(SmallInteger, nullable=False, default=0)

    started_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vod = relationship("VodORM", back_populates="processing_history")


class ChzzkChannelORM(Base):
    __tablename__ = "chzzk_channels"

    id = Column(BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    channel_id = Column(String(100), unique=True, nullable=False)
    channel_name = Column(String(100), nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    channel = relationship("ChannelORM", back_populates="chzzk_channel")
    vods = relationship("ChzzkVodORM", back_populates="channel", cascade="all, delete-orphan")


class ChzzkVodORM(Base):
    __tablename__ = "chzzk_vods"

    id = Column(BigInteger, ForeignKey("vods.id", ondelete="CASCADE"), primary_key=True)
    channel_id = Column(BigInteger, ForeignKey("chzzk_channels.id", ondelete="CASCADE"), nullable=False, index=True)
    video_no = Column(StringAsInt, unique=True, nullable=False)
    video_title = Column(String(255), nullable=False)
    duration = Column(Integer, nullable=False)
    video_category_value = Column(String(100))
    publish_date = Column(DateTime(timezone=True))
    live_open_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    vod = relationship("VodORM", back_populates="chzzk_vod")
    channel = relationship("ChzzkChannelORM", back_populates="vods")
    chat_analytics = relationship(
        "ChzzkVodChatAnalyticsORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )
    asr_analytics = relationship(
        "ChzzkVodAsrAnalyticsORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )


class ChzzkVodChatAnalyticsORM(Base):
    __tablename__ = "chzzk_vod_chat_analytics"

    id = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), primary_key=True)
    total_chat_count = Column(Integer, nullable=False)
    chat_os_type_counts = Column(JSONB, nullable=False)
    chat_participant_count = Column(Integer, nullable=False)
    chat_participant_chat_counts = Column(JSONB, nullable=False)
    chat_count_by_subscription = Column(JSONB, nullable=False)
    hidden_chat_count = Column(Integer, nullable=False)
    avg_chat_count_per_minute = Column(Float, nullable=False)
    total_donation_count = Column(Integer, nullable=False)
    total_donation_amount = Column(Float, nullable=False)
    donor_count = Column(Integer, nullable=False)
    anonymous_donation_amount = Column(Float, nullable=False)
    anonymous_donation_count = Column(Integer, nullable=False)
    avg_donation_amount = Column(Float, nullable=False)
    avg_donation_count_per_minute = Column(Float, nullable=False)
    mission_stats = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    vod = relationship("ChzzkVodORM", back_populates="chat_analytics")


class ChzzkVodAsrAnalyticsORM(Base):
    __tablename__ = "chzzk_vod_asr_analytics"

    id = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), primary_key=True)
    total_speech_time_ms = Column(BigInteger, nullable=False)
    avg_speech_time_per_minute = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    vod = relationship("ChzzkVodORM", back_populates="asr_analytics")
