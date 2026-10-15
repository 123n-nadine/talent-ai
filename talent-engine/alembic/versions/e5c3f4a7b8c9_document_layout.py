"""document layout (lines, boxes, confidence) and preview pdf

Revision ID: e5c3f4a7b8c9
Revises: d4b2e3f6a7b8
Create Date: 2026-10-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5c3f4a7b8c9"
down_revision: Union[str, None] = "d4b2e3f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("layout", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True))
    op.add_column("documents", sa.Column("preview_sha256", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "preview_sha256")
    op.drop_column("documents", "layout")
