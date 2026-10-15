"""criterion result: form level, cv level and verified cv quote

Revision ID: d4b2e3f6a7b8
Revises: c3a1d2e4f5a6
Create Date: 2026-10-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4b2e3f6a7b8"
down_revision: Union[str, None] = "c3a1d2e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("criterion_results", sa.Column("form_level", sa.Integer(), nullable=True))
    op.add_column("criterion_results", sa.Column("cv_level", sa.Integer(), nullable=True))
    op.add_column("criterion_results", sa.Column("cv_quote", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("criterion_results", "cv_quote")
    op.drop_column("criterion_results", "cv_level")
    op.drop_column("criterion_results", "form_level")
