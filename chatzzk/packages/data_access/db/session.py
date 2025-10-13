from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# This global variable will be populated by the application's entry point at startup.
# It acts as a placeholder for the session factory configured for the running app instance.
session_factory: sessionmaker[Session] | None = None


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise RuntimeError("Database session factory is not initialized.")

    db: Session | None = None
    try:
        db = session_factory()
        yield db
    finally:
        if db:
            db.close()
