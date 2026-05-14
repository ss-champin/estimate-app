"""billing_plans table for plan limits and stripe price ids

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=True),
        sa.Column("daily_request_limit", sa.Integer(), nullable=True),
        sa.Column("monthly_request_limit", sa.Integer(), nullable=False),
        sa.Column("estimate_plan_key", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO billing_plans (
                slug, display_name, description,
                stripe_price_id, daily_request_limit, monthly_request_limit,
                estimate_plan_key, sort_order
            ) VALUES
            (
                'free', '無料', 'まずは試したい方向け',
                NULL, NULL, 3,
                'free', 0
            ),
            (
                'paid', 'Pro', 'フル機能・高品質AI',
                NULL, 10, 30,
                'paid', 10
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_table("billing_plans")
