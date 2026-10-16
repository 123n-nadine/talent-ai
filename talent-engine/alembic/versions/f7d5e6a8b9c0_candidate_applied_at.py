"""candidate applied_at (application time from the host system)

Revision ID: f7d5e6a8b9c0
Revises: e5c3f4a7b8c9
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f7d5e6a8b9c0"
down_revision: Union[str, None] = "e5c3f4a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "applied_at")
