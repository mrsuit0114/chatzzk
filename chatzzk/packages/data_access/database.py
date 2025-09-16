import os
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 1. ORM 모델 임포트
from chatzzk.packages.schemas.db_models import (
    Base,
)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set.")

engine = create_engine(DATABASE_URL, pool_recycle=3600, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Session:
    """DB 세션을 안전하게 사용하고 닫기 위한 컨텍스트 매니저."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """DB에 정의된 모든 테이블을 생성합니다. (최초 1회 실행용)"""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.success("Database tables initialized successfully.")
