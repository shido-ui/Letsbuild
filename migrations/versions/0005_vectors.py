"""Add vector embedding storage for semantic retrieval.

Revision ID: 0005_vectors
Revises: 0004_auth
"""
from alembic import op
import sqlalchemy as sa

revision="0005_vectors"
down_revision="0004_auth"
branch_labels=None
depends_on=None

def _columns(table_name:str)->set[str]:
    return {row[1] for row in op.get_bind().exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()}

def upgrade()->None:
    for table in ("questions","topics","concepts"):
        if "embedding" not in _columns(table):
            op.add_column(table,sa.Column("embedding",sa.LargeBinary(),nullable=True))

def downgrade()->None:
    for table in ("concepts","topics","questions"):
        if "embedding" in _columns(table):
            op.drop_column(table,"embedding")
