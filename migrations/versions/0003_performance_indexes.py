"""Add performance indexes for hot local-workspace queries."""
from alembic import op
import sqlalchemy as sa

revision = "0003_performance_indexes"
down_revision = "0002_search_engine"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index("ix_analytics_kb_occurred", "analytics_events", ["knowledge_base_id", "occurred_at"])
    op.create_index("ix_practice_kb_started", "practice_sessions", ["knowledge_base_id", "started_at"])
    op.create_index("ix_review_kb_status_created", "review_items", ["knowledge_base_id", "status", "created_at"])
    op.create_index("ix_ai_provider_user_enabled", "ai_providers", ["user_id", "enabled"])

def downgrade() -> None:
    op.drop_index("ix_ai_provider_user_enabled", table_name="ai_providers")
    op.drop_index("ix_review_kb_status_created", table_name="review_items")
    op.drop_index("ix_practice_kb_started", table_name="practice_sessions")
    op.drop_index("ix_analytics_kb_occurred", table_name="analytics_events")
