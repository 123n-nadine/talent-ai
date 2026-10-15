"""tenant judge prompt

Revision ID: c3a1d2e4f5a6
Revises: beea87c6db42
Create Date: 2026-10-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3a1d2e4f5a6"
down_revision: Union[str, None] = "beea87c6db42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("judge_prompt", sa.String(length=40), nullable=False, server_default="judge-v1"))


def downgrade() -> None:
    op.drop_column("tenants", "judge_prompt")
