"""apply_baseline_sql_logic

Revision ID: 236bfdffb57e
Revises: 89b8bb695807
Create Date: 2026-01-23 11:19:36.669163

"""

from collections.abc import Sequence

from utils import load_sql_file

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "236bfdffb57e"
down_revision: str | Sequence[str] | None = "89b8bb695807"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. 제약조건 (Foreign Key)
    # auth.users와 public.users 연결
    load_sql_file("alembic/sql/baseline/005_constraints.sql")

    # 2. 함수 (Business Logic)
    # 회원가입 핸들러, 검색, 조회 등 핵심 함수 정의
    load_sql_file("alembic/sql/baseline/010_functions.sql")

    # 3. 트리거 (Event Listener)
    # auth.users INSERT 시 handle_new_user 실행
    load_sql_file("alembic/sql/baseline/020_triggers.sql")

    # 4. RLS 활성화 (Row Level Security)
    # 모든 테이블에 대해 RLS Enable (기본 차단)
    load_sql_file("alembic/sql/baseline/030_rls.sql")

    # 5. 초기 권한 부여 (Permissions)
    load_sql_file("alembic/sql/baseline/035_permissions.sql")

    # 6. 정책 (Policies)
    # 실제 접근 권한 규칙 정의 (최적화된 버전)
    load_sql_file("alembic/sql/baseline/040_policies.sql")


def downgrade() -> None:
    # =========================================================
    # Upgrade의 역순으로 롤백 진행
    # =========================================================

    # 5. & 4. Policies 및 RLS 롤백
    # 정책을 하나씩 DROP 하기보다, 테이블의 RLS를 비활성화(DISABLE)하면
    # 정책도 무효화되므로 가장 확실하고 깔끔한 롤백 방법입니다.
    target_tables = ["platforms", "users", "channels", "channel_metadata", "vods", "vod_pipeline_logs"]
    for table in target_tables:
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;")

    # 3. 트리거 삭제
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;")

    # 2. 함수 삭제
    # 010_functions.sql 에서 생성한 모든 함수를 명시적으로 삭제합니다.
    # CASCADE 옵션을 주어 의존성이 있는 객체가 있다면 함께 정리합니다.
    funcs_to_drop = [
        "public.handle_new_user()",
        "public.search_vods",
        "public.search_channels",
        "public.get_channel_detail",
        "public.get_my_channel",
        "public.update_vod_exposure",
        "public.get_my_vods",
        "public.update_channel_metadata",
    ]

    for func in funcs_to_drop:
        # 오버로딩 등의 이슈 방지를 위해 함수 이름만으로 DROP (CASCADE 필수)
        op.execute(f"DROP FUNCTION IF EXISTS {func} CASCADE;")

    # 1. 제약조건 삭제
    op.execute("ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_supabase_uid_fkey;")
