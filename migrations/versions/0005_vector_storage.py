"""Add local vector embedding storage for semantic retrieval."""

from alembic import op
import sqlalchemy as sa

revision = "0005_vector_storage"
down_revision = "0004_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vector_embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("knowledge_base_id", sa.String(36), nullable=False),
        sa.Column("object_id", sa.String(36), nullable=False),
        sa.Column("object_kind", sa.String(40), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vector_embeddings_kb", "vector_embeddings", ["knowledge_base_id"])
    op.create_index(
        "ix_vector_embeddings_object",
        "vector_embeddings",
        ["object_kind", "object_id"],
        unique=True,
    )
    op.create_index(
        "ix_vector_embeddings_content_hash",
        "vector_embeddings",
        ["knowledge_base_id", "content_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_vector_embeddings_content_hash", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_object", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_kb", table_name="vector_embeddings")
    op.drop_table("vector_embeddings")
