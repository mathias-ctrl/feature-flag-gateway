"""create feature flags

Revision ID: 0001
Revises:
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "environment", "key", name="uq_feature_flag_scope"),
    )
    op.create_index("ix_feature_flags_lookup", "feature_flags", ["tenant_id", "environment", "key"])
    op.create_index("ix_feature_flags_tenant_id", "feature_flags", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_feature_flags_tenant_id", table_name="feature_flags")
    op.drop_index("ix_feature_flags_lookup", table_name="feature_flags")
    op.drop_table("feature_flags")
