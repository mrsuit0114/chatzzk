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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB  # PostgreSQL의 JSONB 타입을 위해 import
from sqlalchemy.orm import DeclarativeBase, registry, relationship

from chatzzk.packages.constants.service_codes import VodProcessStatus

# 1. Registry 및 Base 설정 (기존과 동일)
mapper_registry = registry()


class Base(DeclarativeBase):
    registry = mapper_registry
    metadata = mapper_registry.metadata


# 2. 신규 테이블: PlatformORM (마스터 데이터)
class PlatformORM(Base):
    __tablename__ = "platforms"

    id = Column(SmallInteger, primary_key=True)
    platform_code = Column(String(50), unique=True, nullable=False)
    platform_name = Column(String(100), nullable=False)
    donation_unit = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# 3. 신규 테이블: ChzzkChannelORM
class ChzzkChannelORM(Base):
    __tablename__ = "chzzk_channels"

    id = Column(BigInteger, primary_key=True)
    channel_id = Column(String(255), unique=True, nullable=False, index=True)
    channel_name = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False, index=True)  # 수집 대상 필터링을 위해 인덱스 추가
    is_exposure_default = Column(Boolean, default=True)
    allow_detailed_stats = Column(Boolean, default=False)

    # 요약용 메타데이터 (JSONB)
    channel_metadata = Column(JSONB, nullable=True)

    # 효율적인 VOD 탐색용 타임스탬프
    last_vod_crawled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 1:N 관계 설정 (채널은 여러 VOD를 가짐)
    vods = relationship("ChzzkVodORM", back_populates="channel", cascade="all, delete-orphan")


# 4. 리팩토링된 테이블: ChzzkVodORM (기존 2개 테이블 통합)
class ChzzkVodORM(Base):
    __tablename__ = "chzzk_vods"

    id = Column(BigInteger, primary_key=True)
    video_no = Column(String(255), unique=True, nullable=False, index=True)
    video_title = Column(String(500))
    duration = Column(Integer)
    video_category_value = Column(String(100))
    publish_date = Column(DateTime(timezone=True))
    live_open_date = Column(DateTime(timezone=True))

    # N:1 관계 설정 (VOD는 하나의 채널에 속함)
    channel_pk = Column(BigInteger, ForeignKey("chzzk_channels.id", ondelete="CASCADE"), nullable=False)
    channel = relationship("ChzzkChannelORM", back_populates="vods")

    process_status = Column(
        Enum(VodProcessStatus, name="vod_process_status_enum", native_enum=False),
        nullable=False,
        default=VodProcessStatus.PENDING,
        index=True,
    )
    status_details = Column(JSONB, nullable=True)  # 파이프라인 단계별 세부 상태

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 최종 완료/실패 시간

    # 1:1 관계 설정 (VOD는 하나의 분석 결과를 가짐)
    analysis_result = relationship(
        "ChzzkAnalysisResultORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )


# 5. 신규 테이블: ChzzkAnalysisResultORM
class ChzzkAnalysisResultORM(Base):
    __tablename__ = "chzzk_analysis_results"

    id = Column(BigInteger, primary_key=True)

    # 1:1 관계 설정
    vod_pk = Column(BigInteger, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), unique=True, nullable=False)
    vod = relationship("ChzzkVodORM", back_populates="analysis_result")

    is_public = Column(Boolean, nullable=True)  # NULL이면 채널 설정 따름

    # 결과 파일 경로들
    context_file_key = Column(String(1024), nullable=False)
    summary_file_key = Column(String(1024), nullable=True)
    meta_summary_file_key = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


mapper_registry.configure()
