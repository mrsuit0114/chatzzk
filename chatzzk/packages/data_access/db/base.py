from loguru import logger
from sqlalchemy import Engine

# ORM 모델 임포트
from chatzzk.packages.schemas.db_models import Base


def create_all_tables(engine: Engine):
    """DB에 정의된 모든 테이블을 생성합니다. (최초 1회 실행용)"""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.success("Database tables initialized successfully.")
