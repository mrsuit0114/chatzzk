"""redesign vod analytics and processing status

Revision ID: 7c02192b91f7
Revises: 894339690d32
Create Date: 2025-09-26 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7c02192b91f7"
down_revision: str | None = "894339690d32"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Define the Enum type object
    vod_process_status_enum = sa.Enum("PENDING", "PROCESSING", "SUCCESS", "FAILED", name="vod_process_status_enum")

    # 1. Create chzzk_vod_analytics table
    op.create_table(
        "chzzk_vod_analytics",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("vod_pk", sa.BigInteger(), nullable=False),
        sa.Column("total_chat_count", sa.Integer(), nullable=True),
        sa.Column("total_donation_count", sa.Integer(), nullable=True),
        sa.Column("total_donation_amount", sa.Integer(), nullable=True),
        sa.Column("donor_count", sa.Integer(), nullable=True),
        sa.Column("anonymous_donation_amount", sa.Integer(), nullable=True),
        sa.Column("anonymous_donation_count", sa.Integer(), nullable=True),
        sa.Column("chat_os_type_counts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("chat_participant_count", sa.Integer(), nullable=True),
        sa.Column("chat_participant_subscription_counts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("chat_count_by_subscription", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("chat_participant_chat_counts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("mission_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hidden_chat_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(
            ["vod_pk"], ["chzzk_vods.id"], name=op.f("fk_chzzk_vod_analytics_vod_pk_chzzk_vods"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chzzk_vod_analytics")),
    )
    op.create_index(op.f("ix_chzzk_vod_analytics_vod_pk"), "chzzk_vod_analytics", ["vod_pk"], unique=True)

    # 2. Create chzzk_vod_processing_status table with a temporary process_status type
    op.create_table(
        "chzzk_vod_processing_status",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("vod_pk", sa.BigInteger(), nullable=False),
        sa.Column("process_status", sa.String(length=50), nullable=False),  # Temporary String type
        sa.Column("status_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(
            ["vod_pk"],
            ["chzzk_vods.id"],
            name=op.f("fk_chzzk_vod_processing_status_vod_pk_chzzk_vods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chzzk_vod_processing_status")),
    )
    op.create_index(
        op.f("ix_chzzk_vod_processing_status_vod_pk"), "chzzk_vod_processing_status", ["vod_pk"], unique=True
    )

    # 3. Data migration
    op.execute(
        """
        INSERT INTO chzzk_vod_processing_status (vod_pk, process_status, status_details, created_at, updated_at)
        SELECT id, process_status, status_details, created_at, updated_at
        FROM chzzk_vods
        """
    )

    # 4. Create the ENUM type in the database if it doesn't exist
    vod_process_status_enum.create(op.get_bind(), checkfirst=True)

    # 5. Alter column to final Enum type to apply CHECK constraint
    op.alter_column(
        "chzzk_vod_processing_status",
        "process_status",
        type_=vod_process_status_enum,
        existing_type=sa.String(length=50),
        postgresql_using="process_status::vod_process_status_enum",
    )
    op.create_index(
        op.f("ix_chzzk_vod_processing_status_process_status"),
        "chzzk_vod_processing_status",
        ["process_status"],
        unique=False,
    )

    # 6. Drop old columns from chzzk_vods
    op.drop_index("ix_chzzk_vods_process_status", table_name="chzzk_vods")
    op.drop_column("chzzk_vods", "process_status")
    op.drop_column("chzzk_vods", "status_details")

    # 7. Create foreign keys with ON DELETE CASCADE (assuming they don't exist)
    with op.batch_alter_table("chzzk_chat_entries", schema=None) as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_chzzk_chat_entries_vod_pk_chzzk_vods"),
            "chzzk_vods",
            ["vod_pk"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("chzzk_asr_entries", schema=None) as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_chzzk_asr_entries_vod_pk_chzzk_vods"),
            "chzzk_vods",
            ["vod_pk"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("chzzk_summaries", schema=None) as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_chzzk_summaries_vod_pk_chzzk_vods"),
            "chzzk_vods",
            ["vod_pk"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("chzzk_meta_summaries", schema=None) as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_chzzk_meta_summaries_vod_pk_chzzk_vods"),
            "chzzk_vods",
            ["vod_pk"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    # Define the Enum type object to be able to use it
    vod_process_status_enum = sa.Enum("PENDING", "PROCESSING", "SUCCESS", "FAILED", name="vod_process_status_enum")

    # Revert Foreign Key changes
    with op.batch_alter_table("chzzk_meta_summaries", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("fk_chzzk_meta_summaries_vod_pk_chzzk_vods"), type_="foreignkey")

    with op.batch_alter_table("chzzk_summaries", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("fk_chzzk_summaries_vod_pk_chzzk_vods"), type_="foreignkey")

    with op.batch_alter_table("chzzk_asr_entries", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("fk_chzzk_asr_entries_vod_pk_chzzk_vods"), type_="foreignkey")

    with op.batch_alter_table("chzzk_chat_entries", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("fk_chzzk_chat_entries_vod_pk_chzzk_vods"), type_="foreignkey")

    # Add columns back to chzzk_vods
    op.add_column(
        "chzzk_vods",
        sa.Column("status_details", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )
    op.add_column(
        "chzzk_vods",
        sa.Column(
            "process_status",
            sa.String(length=50),
            autoincrement=False,
            nullable=True,
        ),
    )

    # Data migration back to chzzk_vods
    op.execute(
        """
        UPDATE chzzk_vods v
        SET process_status = ps.process_status, status_details = ps.status_details
        FROM chzzk_vod_processing_status ps
        WHERE v.id = ps.vod_pk
        """
    )

    # CORRECTED ORDER STARTS HERE
    # 1. Alter column type to Enum first
    op.alter_column(
        "chzzk_vods",
        "process_status",
        type_=vod_process_status_enum,
        existing_type=sa.String(length=50),
        postgresql_using="process_status::vod_process_status_enum",
    )

    # 2. Now, apply nullable and server_default constraints
    op.alter_column("chzzk_vods", "process_status", nullable=False, server_default="PENDING")

    op.create_index("ix_chzzk_vods_process_status", "chzzk_vods", ["process_status"], unique=False)

    # Drop new tables
    op.drop_index(op.f("ix_chzzk_vod_processing_status_vod_pk"), table_name="chzzk_vod_processing_status")
    op.drop_index(op.f("ix_chzzk_vod_processing_status_process_status"), table_name="chzzk_vod_processing_status")
    op.drop_table("chzzk_vod_processing_status")

    op.drop_index(op.f("ix_chzzk_vod_analytics_vod_pk"), table_name="chzzk_vod_analytics")
    op.drop_table("chzzk_vod_analytics")

    # DO NOT drop the enum type as it is needed by the revision we are downgrading to.
