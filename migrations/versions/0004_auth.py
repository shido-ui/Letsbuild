"""Add authenticated local account fields.

Revision ID: 0004_auth
Revises: 0003_performance_indexes
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_auth"
down_revision = "0003_performance_indexes"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    bind = op.get_bind()
    return {row[1] for row in bind.exec_driver_sql("PRAGMA table_info(users)").fetchall()}


def upgrade() -> None:
    columns = _columns()
    if "username" not in columns:
        op.add_column("users", sa.Column("username", sa.String(64), nullable=True))
    if "hashed_password" not in columns:
        op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))
    if "is_active" not in columns:
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    indexes = {row[1] for row in op.get_bind().exec_driver_sql("PRAGMA index_list(users)").fetchall()}
    if "ix_users_username" not in indexes:
        op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    indexes = {row[1] for row in op.get_bind().exec_driver_sql("PRAGMA index_list(users)").fetchall()}
    if "ix_users_username" in indexes:
        op.drop_index("ix_users_username", table_name="users")
    columns = _columns()
    for name in ("is_active", "hashed_password", "username"):
        if name in columns:
            op.drop_column("users", name)
