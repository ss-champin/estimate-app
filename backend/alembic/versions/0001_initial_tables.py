"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-03-28
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("users",
        sa.Column("id",         sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clerk_id",   sa.String(255), nullable=False),
        sa.Column("email",      sa.String(255), nullable=False),
        sa.Column("plan",       sa.Enum("free","paid", name="plan_enum"), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("clerk_id"), sa.UniqueConstraint("email"),
    )
    op.create_table("subscriptions",
        sa.Column("id",                     sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",                sa.UUID(), nullable=False),
        sa.Column("stripe_customer_id",     sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("status",                 sa.Enum("active","canceled","past_due", name="subscription_status_enum"), nullable=False, server_default="active"),
        sa.Column("current_period_end",     sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",             sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",             sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["user_id"],["users.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS subscription_status_enum")
    op.execute("DROP TYPE IF EXISTS plan_enum")
