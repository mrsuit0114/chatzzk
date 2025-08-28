import os

from chatzzk.packages.data_access.database import create_all_tables, engine

# .env 로드를 위한 import
from dotenv import load_dotenv
from loguru import logger


def initialize_database():
    """
    데이터베이스에 연결하고 모든 테이블을 생성합니다.
    로컬 실행 시 .env 파일에서 환경 변수를 로드하고,
    Docker 환경에서는 주입된 환경 변수를 사용합니다.
    """
    # 1. .env 파일 로드
    #    스크립트 실행 위치(프로젝트 루트)를 기준으로 .env 파일 경로를 찾습니다.
    project_root = os.getcwd()
    dotenv_path = os.path.join(project_root, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.info("Loaded environment variables from .env file.")

    logger.info("Initializing database...")
    try:
        # 2. 연결 테스트
        with engine.connect() as _connection:  # 사용하지 않는 변수는 '_' 사용
            logger.success("✅ Database connection successful.")

        # 3. 테이블 생성
        create_all_tables()
        # create_all_tables 내부의 로그가 있으므로 중복 로그 제거 가능
        # logger.success("✅ All tables created successfully.")

    except Exception as e:
        logger.opt(exception=True).error(f"❌ DB initialization failed: {e}")
        # 실패 시 0이 아닌 종료 코드를 반환하여 docker-compose가 실패를 인지하게 함
        exit(1)


if __name__ == "__main__":
    initialize_database()
