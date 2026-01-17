import os

from alembic import op


def load_sql_file(file_path: str):
    """
    alembic/ 디렉토리를 기준으로 상대 경로의 SQL 파일을 읽어서 실행
    예: file_path = "sql/baseline/010_functions.sql"
    """
    # 현재 실행 위치(alembic.ini가 있는 곳) 기준 혹은 파일 기준 경로 설정
    # 여기서는 alembic 폴더 내부 구조를 가정
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # alembic/ 폴더
    full_path = os.path.join(base_dir, file_path)

    try:
        with open(full_path, encoding="utf-8") as f:
            sql = f.read()
            # 빈 파일이 아닐 경우 실행
            if sql.strip():
                op.execute(sql)
    except FileNotFoundError:
        print(f"Warning: SQL file not found at {full_path}")
        raise
