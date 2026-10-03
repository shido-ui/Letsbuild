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


def _columns(bind) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns("users")}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind)

    if "username" not in columns:
        op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
        op.execute("UPDATE users SET username = 'legacy_' || substr(id, 1, 12) WHERE username IS NULL")
        op.create_unique_constraint("uq_users_username", "users", ["username"])

    if "hashed_password" not in columns:
        op.add_column("users", sa.Column("hashed_password", sa.Text(), nullable=True))

    if "is_active" not in columns:
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )

    if "display_name" not in columns:
        op.add_column("users", sa.Column("display_name", sa.String(length=200), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind)

    if "display_name" in columns:
        op.drop_column("users", "display_name")
    if "is_active" in columns:
        op.drop_column("users", "is_active")
    if "hashed_password" in columns:
        op.drop_column("users", "hashed_password")

    if "username" in columns:
        constraints = {c.get("name") for c in sa.inspect(bind).get_unique_constraints("users")}
        if "uq_users_username" in constraints:
            op.drop_constraint("uq_users_username", "users", type_="unique")
        op.drop_column("users", "username")
