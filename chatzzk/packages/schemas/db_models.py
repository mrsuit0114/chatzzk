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
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

from chatzzk.packages.constants.service_codes import (
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

    process_status = Column(
        Enum(VodProcessStatus, name="vod_process_status_enum", native_enum=False),
        nullable=False,
        default=VodProcessStatus.PENDING,
        index=True,
    )
    status_details = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chat_entries = relationship("ChzzkChatEntryORM", back_populates="vod", cascade="all, delete-orphan")
    asr_entries = relationship("ChzzkAsrEntryORM", back_populates="vod", cascade="all, delete-orphan")


class ChzzkChatEntryORM(Base):
    __tablename__ = "chzzk_chat_entries"

    id = Column(BigInteger, primary_key=True)
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChzzkAsrEntryORM(Base):
    __tablename__ = "chzzk_asr_entries"

    id = Column(BigInteger, primary_key=True)
    start_ms = Column(BigInteger, nullable=False)
    end_ms = Column(BigInteger, nullable=False)
    timestamp_ms = Column(BigInteger, index=True)
    content = Column(Text)

    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), nullable=False)
    vod = relationship("ChzzkVodORM", back_populates="asr_entries")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
