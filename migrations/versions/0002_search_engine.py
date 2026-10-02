"""Add the structured ModuleIQ search index."""

from alembic import op
import sqlalchemy as sa

revision = "0002_search_engine"
down_revision = "0001_initial_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_entries",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("knowledge_base_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("object_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_document_id", sa.String(36)),
        sa.Column("source_page_id", sa.String(36)),
    )
    op.create_index("ix_search_entries_kb", "search_entries", ["knowledge_base_id"])
    op.create_index("ix_search_entries_kind", "search_entries", ["kind"])
    op.create_index("ix_search_entries_object", "search_entries", ["object_id"])

    op.create_table(
        "search_index_state",
        sa.Column("knowledge_base_id", sa.String(36), primary_key=True),
        sa.Column("source_fingerprint", sa.String(64), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
    )

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        bind.exec_driver_sql(
            "CREATE VIRTUAL TABLE search_entries_fts USING fts5("
            "entry_id UNINDEXED, knowledge_base_id UNINDEXED, kind UNINDEXED, "
            "object_id UNINDEXED, title, content, tokenize='unicode61'"
            ")"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        bind.exec_driver_sql("DROP TABLE IF EXISTS search_entries_fts")
    op.drop_table("search_index_state")
    op.drop_index("ix_search_entries_object", table_name="search_entries")
    op.drop_index("ix_search_entries_kind", table_name="search_entries")
    op.drop_index("ix_search_entries_kb", table_name="search_entries")
    op.drop_table("search_entries")
