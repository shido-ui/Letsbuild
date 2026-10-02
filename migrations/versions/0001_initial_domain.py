"""Create canonical ModuleIQ Phase 2 domain schema."""
from alembic import op

revision = "0001_initial_domain"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    from moduleiq.infrastructure.database.base import Base
    from moduleiq.infrastructure.database import models_import  # noqa: F401
    Base.metadata.create_all(op.get_bind(), checkfirst=True)

def downgrade() -> None:
    from moduleiq.infrastructure.database.base import Base
    from moduleiq.infrastructure.database import models_import  # noqa: F401
    Base.metadata.drop_all(op.get_bind(), checkfirst=True)
