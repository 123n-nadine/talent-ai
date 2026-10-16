"""embedding: source screening and text hash (talent pool)

Revision ID: a8e6f7b9c0d1
Revises: f7d5e6a8b9c0
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a8e6f7b9c0d1"
down_revision: Union[str, None] = "f7d5e6a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("embeddings", sa.Column("screening_id", sa.String(length=40), nullable=True))
    op.add_column("embeddings", sa.Column("text_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("embeddings", "text_hash")
    op.drop_column("embeddings", "screening_id")
