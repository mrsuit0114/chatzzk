"""Create video_context_entries view

Revision ID: 05c25f775603
Revises: 87aa2d17a45e
Create Date: 2025-09-23 17:55:10.009537

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "05c25f775603"
down_revision: str | Sequence[str] | None = "87aa2d17a45e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE VIEW video_context_entries AS
        SELECT
            'chat' AS entry_type,
            id,
            vod_pk,
            timestamp_ms,
            content
        FROM chzzk_chat_entries
        UNION ALL
        SELECT
            'asr' AS entry_type,
            id,
            vod_pk,
            timestamp_ms,
            content
        FROM chzzk_asr_entries;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP VIEW IF EXISTS video_context_entries;")
