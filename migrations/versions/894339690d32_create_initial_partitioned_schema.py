"""Create initial partitioned schema

Revision ID: 894339690d32
Revises:
Create Date: 2025-09-23 20:20:08.089413

"""

import datetime
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from chatzzk.packages.schemas.db_models import StringAsInt

# revision identifiers, used by Alembic.
revision: str = "894339690d32"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### Part 1: Create non-partitioned tables ###
    op.create_table(
        "platforms",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("platform_code", sa.String(length=50), nullable=False),
        sa.Column("platform_name", sa.String(length=100), nullable=False),
        sa.Column("donation_unit", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform_code"),
    )
    op.create_table(
        "chzzk_channels",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("platform_id", sa.SmallInteger(), nullable=False),
        sa.Column("channel_id", sa.String(length=255), nullable=False),
        sa.Column("channel_name", sa.String(length=255), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("allow_data_collection", sa.Boolean(), nullable=True),
        sa.Column("is_exposure_default", sa.Boolean(), nullable=True),
        sa.Column("allow_detailed_stats", sa.Boolean(), nullable=True),
        sa.Column("channel_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_vod_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(
            ["platform_id"],
            ["platforms.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_chzzk_channels_allow_data_collection"), "chzzk_channels", ["allow_data_collection"], unique=False
    )
    op.create_index(op.f("ix_chzzk_channels_channel_id"), "chzzk_channels", ["channel_id"], unique=True)
    op.create_index(op.f("ix_chzzk_channels_platform_id"), "chzzk_channels", ["platform_id"], unique=False)
    op.create_table(
        "chzzk_vods",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("video_no", StringAsInt(), nullable=False),
        sa.Column("video_title", sa.String(length=500), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("video_category_value", sa.String(length=100), nullable=True),
        sa.Column("publish_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("live_open_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel_pk", sa.BigInteger(), nullable=False),
        sa.Column(
            "process_status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="vod_process_status_enum", native_enum=False),
            nullable=False,
        ),
        sa.Column("status_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["channel_pk"], ["chzzk_channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chzzk_vods_process_status"), "chzzk_vods", ["process_status"], unique=False)
    op.create_index(op.f("ix_chzzk_vods_video_no"), "chzzk_vods", ["video_no"], unique=True)

    # ### Part 2: Create partitioned tables using raw SQL ###
    op.execute("""
        CREATE TABLE chzzk_chat_entries (
            id BIGINT NOT NULL, timestamp_ms BIGINT NOT NULL, content TEXT, os_type VARCHAR, pay_amount INTEGER,
            nickname VARCHAR(255), user_role_code VARCHAR, subscription_tier INTEGER, subscription_accumulative_month INTEGER,
            message_type_code SMALLINT, user_id_hash VARCHAR(255), vod_pk BIGINT NOT NULL,
            vod_live_open_date TIMESTAMP WITH TIME ZONE NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, PRIMARY KEY (id, vod_live_open_date)
        ) PARTITION BY RANGE (vod_live_open_date);
    """)
    op.execute(
        "CREATE INDEX ix_chzzk_chat_entries_vod_live_open_date ON chzzk_chat_entries USING btree (vod_live_open_date);"
    )
    op.execute("CREATE INDEX ix_chzzk_chat_entries_vod_pk ON chzzk_chat_entries USING btree (vod_pk);")

    op.execute("""
        CREATE TABLE chzzk_asr_entries (
            id BIGINT NOT NULL, start_ms BIGINT NOT NULL, end_ms BIGINT NOT NULL, timestamp_ms BIGINT, content TEXT,
            vod_pk BIGINT NOT NULL, vod_live_open_date TIMESTAMP WITH TIME ZONE NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, PRIMARY KEY (id, vod_live_open_date)
        ) PARTITION BY RANGE (vod_live_open_date);
    """)
    op.execute(
        "CREATE INDEX ix_chzzk_asr_entries_vod_live_open_date ON chzzk_asr_entries USING btree (vod_live_open_date);"
    )
    op.execute("CREATE INDEX ix_chzzk_asr_entries_vod_pk ON chzzk_asr_entries USING btree (vod_pk);")

    op.execute("""
        CREATE TABLE chzzk_summaries (
            id BIGINT NOT NULL, vod_pk BIGINT NOT NULL, start_s INTEGER NOT NULL, end_s INTEGER NOT NULL, content TEXT,
            sentiment VARCHAR, score DOUBLE PRECISION, vod_live_open_date TIMESTAMP WITH TIME ZONE NOT NULL, PRIMARY KEY (id, vod_live_open_date)
        ) PARTITION BY RANGE (vod_live_open_date);
    """)
    op.execute(
        "CREATE INDEX ix_chzzk_summaries_vod_live_open_date ON chzzk_summaries USING btree (vod_live_open_date);"
    )
    op.execute("CREATE INDEX ix_chzzk_summaries_vod_pk ON chzzk_summaries USING btree (vod_pk);")

    op.execute("""
        CREATE TABLE chzzk_meta_summaries (
            id BIGINT NOT NULL, vod_pk BIGINT NOT NULL, start_s INTEGER NOT NULL, end_s INTEGER NOT NULL, content TEXT,
            vod_live_open_date TIMESTAMP WITH TIME ZONE NOT NULL, PRIMARY KEY (id, vod_live_open_date)
        ) PARTITION BY RANGE (vod_live_open_date);
    """)
    op.execute(
        "CREATE INDEX ix_chzzk_meta_summaries_vod_live_open_date ON chzzk_meta_summaries USING btree (vod_live_open_date);"
    )
    op.execute("CREATE INDEX ix_chzzk_meta_summaries_vod_pk ON chzzk_meta_summaries USING btree (vod_pk);")

    # ### Part 3: Create partitions ###
    monthly_tables = ["chzzk_asr_entries", "chzzk_summaries", "chzzk_meta_summaries"]
    start_date = datetime.date(2024, 1, 1)
    for table in monthly_tables:
        op.execute(f"CREATE TABLE {table}_default PARTITION OF {table} DEFAULT;")
        for i in range(24):
            year = start_date.year + (start_date.month + i - 1) // 12
            month = (start_date.month + i - 1) % 12 + 1
            partition_start_date = f"{year}-{month:02d}-01"
            next_month_year = year + (month // 12)
            next_month = month % 12 + 1
            partition_end_date = f"{next_month_year}-{next_month:02d}-01"
            partition_name = f"{table}_{year}_{month:02d}"
            op.execute(
                f""" CREATE TABLE {partition_name} PARTITION OF {table} FOR VALUES FROM ('{partition_start_date}') TO ('{partition_end_date}'); """
            )

    chat_table = "chzzk_chat_entries"
    op.execute(f"CREATE TABLE {chat_table}_default PARTITION OF {chat_table} DEFAULT;")
    current_date = datetime.date(2024, 1, 1)
    for i in range(104):
        start_of_week = current_date + datetime.timedelta(weeks=i)
        end_of_week = start_of_week + datetime.timedelta(weeks=1)
        partition_name = f"{chat_table}_{start_of_week.strftime('%Y_w%U')}"
        op.execute(
            f""" CREATE TABLE {partition_name} PARTITION OF {chat_table} FOR VALUES FROM ('{start_of_week.isoformat()}') TO ('{end_of_week.isoformat()}'); """
        )

    # ### Part 4: Create the view ###
    op.execute("""
        CREATE VIEW video_context_entries AS
        SELECT 'chat' AS entry_type, id, vod_pk, timestamp_ms, content FROM chzzk_chat_entries
        UNION ALL
        SELECT 'asr' AS entry_type, id, vod_pk, timestamp_ms, content FROM chzzk_asr_entries;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS video_context_entries;")
    op.execute("DROP TABLE IF EXISTS chzzk_meta_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS chzzk_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS chzzk_asr_entries CASCADE;")
    op.execute("DROP TABLE IF EXISTS chzzk_chat_entries CASCADE;")
    op.execute("DROP TABLE IF EXISTS chzzk_vods CASCADE;")
    op.execute("DROP TABLE IF EXISTS chzzk_channels CASCADE;")
    op.execute("DROP TABLE IF EXISTS platforms CASCADE;")
