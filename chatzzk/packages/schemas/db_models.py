from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, registry, relationship

from chatzzk.packages.constants.service_codes import WorkflowStatus

# 1. Registry 설정
mapper_registry = registry()


class Base(DeclarativeBase):
    registry = mapper_registry
    metadata = mapper_registry.metadata


class ChzzkVodORM(Base):
    __tablename__ = "chzzk_vods"

    id = Column(Integer, primary_key=True)
    video_no = Column(String, unique=True, index=True, nullable=False)
    video_title = Column(String, nullable=False)
    duration = Column(Integer)
    video_category_value = Column(String)
    channel_id = Column(String, index=True, nullable=False)
    live_open_date = Column(DateTime)
    publish_date = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    status = relationship(
        "ChzzkVodProcessingStatusORM", back_populates="vod", uselist=False, cascade="all, delete-orphan"
    )


class ChzzkVodProcessingStatusORM(Base):
    __tablename__ = "chzzk_vod_processing_status"

    id = Column(Integer, primary_key=True)
    vod_id = Column(Integer, ForeignKey("chzzk_vods.id", ondelete="CASCADE"), unique=True, nullable=False)

    # --- 워크플로우 제어 상태 ---
    # Enum을 사용하기 위해선 별도 설정이 필요하므로, 여기서는 문자열로 저장.
    # 값: PENDING, PROCESSING, SUCCESS, FAILED
    workflow_status = Column(String, default=WorkflowStatus.PENDING_PREPROCESSING, nullable=False, index=True)

    # --- 각 단계별 완료 여부 (Boolean 플래그) ---
    # Boolean 필드는 기본값을 False로 설정하여 명시적으로 True로 변경하도록 유도.
    is_chat_crawled = Column(Boolean, default=False, nullable=False)
    is_mp4_downloaded = Column(Boolean, default=False, nullable=False)
    is_wav_extracted = Column(Boolean, default=False, nullable=False)

    is_asr_completed = Column(Boolean, default=False, nullable=False)
    is_context_saved = Column(Boolean, default=False, nullable=False)
    is_summary_generated = Column(Boolean, default=False, nullable=False)

    # --- 데이터 저장 위치 ---
    # 파일이 아직 생성되지 않았을 수 있으므로 nullable=True
    context_file_path = Column(String, nullable=True)
    summary_file_path = Column(String, nullable=True)

    # --- 타임스탬프 ---
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)  # 워크플로우 최종 완료 시간

    # ChzzkVodORM 객체에 쉽게 접근하기 위한 관계 설정
    vod = relationship("ChzzkVodORM", back_populates="status")


mapper_registry.configure()
