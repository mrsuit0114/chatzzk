from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

from chatzzk.packages.constants.service_codes import (
    Atmosphere,
    ChzzkMessageTypeCode,
    OsType,
    SubscriptionTier,
    UserRoleCode,
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
    chat_entries = relationship("ChzzkChatEntryORM", back_populates="vod", cascade="all, delete-orphan")
    asr_entries = relationship("ChzzkAsrEntryORM", back_populates="vod", cascade="all, delete-orphan")
    summaries = relationship("ChzzkSummaryORM", back_populates="vod", cascade="all, delete-orphan")
    meta_summaries = relationship("ChzzkMetaSummaryORM", back_populates="vod", cascade="all, delete-orphan")


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


class ChzzkChatEntryORM(Base):
    __tablename__ = "chzzk_chat_entries"

    id = Column(BigInteger, autoincrement=True)
    timestamp_ms = Column(BigInteger, nullable=False, index=True)
    content = Column(Text)
    os_type = Column(Enum(OsType, name="os_type_enum", native_enum=False), nullable=True)
    pay_amount = Column(Integer, nullable=True)
    nickname = Column(String(255))
    user_role_code = Column(Enum(UserRoleCode, name="user_role_code_enum", native_enum=False))
    subscription_tier = Column(Enum(SubscriptionTier, name="subscription_tier_enum", native_enum=False), nullable=True)
    subscription_accumulative_month = Column(Integer, nullable=True)
    message_type_code = Column(Enum(ChzzkMessageTypeCode, name="chzzk_message_type_code_enum", native_enum=False))
    user_id_hash = Column(String(255))

    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), nullable=False)
    vod = relationship("ChzzkVodORM", back_populates="chat_entries")
    vod_live_open_date = Column(DateTime(timezone=True), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("id", "vod_live_open_date"),)


class ChzzkAsrEntryORM(Base):
    __tablename__ = "chzzk_asr_entries"

    id = Column(BigInteger, autoincrement=True)
    start_ms = Column(BigInteger, nullable=False)
    end_ms = Column(BigInteger, nullable=False)
    timestamp_ms = Column(BigInteger, index=True)
    content = Column(Text)

    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), nullable=False)
    vod = relationship("ChzzkVodORM", back_populates="asr_entries")
    vod_live_open_date = Column(DateTime(timezone=True), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("id", "vod_live_open_date"),)


class ChzzkSummaryORM(Base):
    __tablename__ = "chzzk_summaries"

    id = Column(BigInteger, autoincrement=True)
    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), nullable=False, index=True)
    start_s = Column(Integer, nullable=False)
    end_s = Column(Integer, nullable=False)
    content = Column(Text)
    atmosphere = Column(Enum(Atmosphere, name="atmosphere_enum", native_enum=False), nullable=True)
    score = Column(Float)

    vod_live_open_date = Column(DateTime(timezone=True), nullable=False, index=True)

    vod = relationship("ChzzkVodORM", back_populates="summaries")

    __table_args__ = (PrimaryKeyConstraint("id", "vod_live_open_date"),)


class ChzzkMetaSummaryORM(Base):
    __tablename__ = "chzzk_meta_summaries"

    id = Column(BigInteger, autoincrement=True)
    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), nullable=False, index=True)
    start_s = Column(Integer, nullable=False)  # 요약들의 시작 시간
    end_s = Column(Integer, nullable=False)  # 요약들의 끝 시간
    content = Column(Text)

    vod_live_open_date = Column(DateTime(timezone=True), nullable=False, index=True)

    vod = relationship("ChzzkVodORM", back_populates="meta_summaries")

    __table_args__ = (PrimaryKeyConstraint("id", "vod_live_open_date"),)
