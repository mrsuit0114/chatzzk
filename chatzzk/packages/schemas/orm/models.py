from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    TypeDecorator,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chatzzk.packages.constants.service_codes import (
    VodProcessStatus,
)


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


class Base(DeclarativeBase):
    pass


class PlatformORM(Base):
    __tablename__ = "platforms"

    id = Column(SmallInteger, primary_key=True)
    platform_code = Column(String(50), unique=True, nullable=False)
    platform_name = Column(String(100), nullable=False)
    donation_unit = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chzzk_channels = relationship("ChzzkChannelORM", back_populates="platform")


class ChzzkChannelORM(Base):
    __tablename__ = "chzzk_channels"

    id = Column(BigInteger, primary_key=True)
    platform_id = Column(SmallInteger, ForeignKey("platforms.id"), nullable=False, index=True)
    channel_id = Column(String(255), unique=True, nullable=False, index=True)
    channel_name = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    allow_data_collection = Column(Boolean, default=False, index=True)
    is_exposure_default = Column(Boolean, default=True)
    allow_detailed_stats = Column(Boolean, default=False)
    channel_metadata = Column(JSONB, nullable=True)
    last_vod_crawled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    platform = relationship("PlatformORM", back_populates="chzzk_channels")
    vods = relationship("ChzzkVodORM", back_populates="channel", cascade="all, delete-orphan")


class ChzzkVodORM(Base):
    __tablename__ = "chzzk_vods"

    id = Column(BigInteger, primary_key=True)
    video_no = Column(StringAsInt, unique=True, nullable=False, index=True)
    video_title = Column(String(500))
    duration = Column(Integer)
    video_category_value = Column(String(100))
    publish_date = Column(DateTime(timezone=True))
    live_open_date = Column(DateTime(timezone=True))

    channel_pk = Column(BigInteger, ForeignKey("chzzk_channels.id", ondelete="CASCADE"), nullable=False)
    channel = relationship("ChzzkChannelORM", back_populates="vods")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    processing_status = relationship(
        "ChzzkVodProcessingStatusORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )
    analytics = relationship("ChzzkVodAnalyticsORM", back_populates="vod", uselist=False, cascade="all, delete-orphan")

    # 스토리지에 저장된 파일들의 키 (경로)
    temp_video_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    temp_audio_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    temp_chat_entries_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    temp_asr_entries_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    final_video_context_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_chat_entries_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_asr_entries_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_summary_entries_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    final_meta_summary_entries_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ChzzkVodProcessingStatusORM(Base):
    __tablename__ = "chzzk_vod_processing_status"

    id = Column(BigInteger, primary_key=True)
    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), unique=True, nullable=False)
    process_status = Column(
        Enum(VodProcessStatus, name="vod_process_status_enum", native_enum=False),
        nullable=False,
        default=VodProcessStatus.PENDING,
        index=True,
    )
    status_details = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vod = relationship("ChzzkVodORM", back_populates="processing_status")


class ChzzkVodAnalyticsORM(Base):
    __tablename__ = "chzzk_vod_analytics"

    id = Column(BigInteger, primary_key=True)
    vod_pk = Column(
        BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    total_chat_count = Column(Integer)
    total_donation_count = Column(Integer)
    total_donation_amount = Column(Integer)
    donor_count = Column(Integer)
    anonymous_donation_amount = Column(Integer)
    anonymous_donation_count = Column(Integer)
    chat_os_type_counts = Column(JSONB)
    chat_participant_count = Column(Integer)
    chat_participant_subscription_counts = Column(JSONB)
    chat_count_by_subscription = Column(JSONB)
    chat_participant_chat_counts = Column(JSONB)
    mission_stats = Column(JSONB)
    hidden_chat_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vod = relationship("ChzzkVodORM", back_populates="analytics")
