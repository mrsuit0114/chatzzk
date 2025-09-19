from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from chatzzk.packages.schemas.db_configs import DatabaseConfig, PostgresConfig


def create_db_engine(db_config: DatabaseConfig) -> Engine:
    if not isinstance(db_config, PostgresConfig):
        raise TypeError(f"Unsupported DB config type: {type(db_config)}")
    return create_engine(db_config.database_url, pool_recycle=3600, pool_pre_ping=True)


def create_db_session_provider(engine: Engine):
    """주어진 SQLAlchemy 엔진으로부터 세션 제공자(컨텍스트 매니저)를 생성합니다."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @contextmanager
    def get_db_session() -> Session:
        """DB 세션을 안전하게 사용하고 닫기 위한 컨텍스트 매니저."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return get_db_session
