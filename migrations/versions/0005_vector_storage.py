"""Add local vector embedding storage for semantic retrieval.

The canonical 0001 migration creates all ORM tables from Base.metadata.
This migration therefore reconciles the vector table/indexes for databases
where that table was not present, while remaining safe for databases that
already received it from the canonical schema bootstrap.
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_vector_storage"
down_revision = "0004_authentication"
branch_labels = None
depends_on = None


def _index_names(bind) -> set[str]:
    inspector = sa.inspect(bind)
    if not inspector.has_table("vector_embeddings"):
        return set()
    return {item["name"] for item in inspector.get_indexes("vector_embeddings")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("vector_embeddings"):
        op.create_table(
            "vector_embeddings",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "knowledge_base_id",
                sa.String(36),
                sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("object_id", sa.String(36), nullable=False),
            sa.Column("object_kind", sa.String(40), nullable=False),
            sa.Column("model_name", sa.String(200), nullable=False),
            sa.Column("dimension", sa.Integer(), nullable=False),
            sa.Column("embedding", sa.LargeBinary(), nullable=False),
            sa.Column("content_hash", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    indexes = _index_names(bind)
    if "ix_vector_embeddings_kb" not in indexes:
        op.create_index(
            "ix_vector_embeddings_kb",
            "vector_embeddings",
            ["knowledge_base_id"],
        )
    if "ix_vector_embeddings_object" not in indexes:
        op.create_index(
            "ix_vector_embeddings_object",
            "vector_embeddings",
            ["object_kind", "object_id"],
            unique=True,
        )
    if "ix_vector_embeddings_content_hash" not in indexes:
        op.create_index(
            "ix_vector_embeddings_content_hash",
            "vector_embeddings",
            ["knowledge_base_id", "content_hash"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vector_embeddings"):
        return

    indexes = _index_names(bind)
    for name in (
        "ix_vector_embeddings_content_hash",
        "ix_vector_embeddings_object",
        "ix_vector_embeddings_kb",
    ):
        if name in indexes:
            op.drop_index(name, table_name="vector_embeddings")

    # 0001 owns the canonical table lifecycle, so only remove the table when
    # it was created by this migration in a database without the canonical
    # bootstrap. Keeping it here would make downgrade unsafe for the current
    # migration architecture.
