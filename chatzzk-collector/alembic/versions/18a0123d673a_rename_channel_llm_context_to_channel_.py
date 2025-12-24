"""rename channel_llm_context to channel_metadata

Revision ID: 18a0123d673a
Revises: efa0d3012a67
Create Date: 2025-12-24 20:39:53.416984

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18a0123d673a"
down_revision: str | Sequence[str] | None = "efa0d3012a67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    # 1️⃣ 테이블 rename
    op.rename_table(
        "channel_llm_contexts",
        "channel_metadata",
    )

    # 2️⃣ 컬럼 rename
    op.alter_column(
        "channel_metadata",
        "llm_context",
        new_column_name="attributes",
    )

    # 3️⃣ FK constraint rename (권장)
    op.execute(
        """
        ALTER TABLE channel_metadata
        RENAME CONSTRAINT channel_llm_contexts_channel_id_fkey
        TO channel_metadata_channel_id_fkey
        """
    )


def downgrade():
    # FK constraint 원복
    op.execute(
        """
        ALTER TABLE channel_metadata
        RENAME CONSTRAINT channel_metadata_channel_id_fkey
        TO channel_llm_contexts_channel_id_fkey
        """
    )

    # 컬럼 원복
    op.alter_column(
        "channel_metadata",
        "attributes",
        new_column_name="llm_context",
    )

    # 테이블 원복
    op.rename_table(
        "channel_metadata",
        "channel_llm_contexts",
    )
