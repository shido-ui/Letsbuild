"""Add authenticated local account fields.

Revision ID: 0004_auth
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_auth"
down_revision = "0003_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "is_active")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "username")
