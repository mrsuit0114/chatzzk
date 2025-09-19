import os

# .env 로드를 위한 import
from dotenv import load_dotenv
from loguru import logger

from chatzzk.packages.data_access.db.base import create_all_tables
from chatzzk.packages.data_access.db.factory import create_db_engine
from chatzzk.packages.schemas.db_configs import PostgresConfig


def initialize_database():
    """
    데이터베이스에 연결하고 모든 테이블을 생성합니다.
    로컬 실행 시 .env 파일에서 환경 변수를 로드하고,
    Docker 환경에서는 주입된 환경 변수를 사용합니다.
    """
    # 1. .env 파일 로드
    project_root = os.getcwd()
    dotenv_path = os.path.join(project_root, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.info("Loaded environment variables from .env file.")

    # 2. 환경 변수에서 DB URL 가져오기
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL environment variable not set.")
        exit(1)

    logger.info("Initializing database...")
    try:
        # 3. 설정 객체 및 DB 엔진 생성
        db_config = PostgresConfig(database_url=db_url)
        engine = create_db_engine(db_config)

        # 4. 연결 테스트
        with engine.connect() as _connection:
            logger.success("✅ Database connection successful.")

        # 5. 테이블 생성
        create_all_tables(engine)

    except Exception as e:
        logger.opt(exception=True).error(f"❌ DB initialization failed: {e}")
        exit(1)


if __name__ == "__main__":
    initialize_database()
