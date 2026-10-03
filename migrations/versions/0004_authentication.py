"""Add application authentication fields to users.

Revision ID: 0004
Revises: 0003_performance_indexes
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_authentication"
down_revision = "0003_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("display_name", sa.String(length=200), nullable=True))
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.execute("UPDATE users SET username = 'legacy_' || substr(id, 1, 12) WHERE username IS NULL")
    op.alter_column("users", "username", nullable=False)


def downgrade() -> None:
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "display_name")
    op.drop_column("users", "is_active")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "username")
