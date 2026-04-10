"""add api_usage table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-28
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("api_usage",
        sa.Column("id",         sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",    sa.UUID(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("count",      sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"],["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id","usage_date", name="uq_api_usage_user_date"),
    )
    op.create_index("ix_api_usage_user_date","api_usage",["user_id","usage_date"])


def downgrade() -> None:
    op.drop_index("ix_api_usage_user_date", table_name="api_usage")
    op.drop_table("api_usage")
