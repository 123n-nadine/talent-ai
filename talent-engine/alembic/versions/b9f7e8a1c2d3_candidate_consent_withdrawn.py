"""candidate consent withdrawal (the AI data is erased, the reference stays)

Revision ID: b9f7e8a1c2d3
Revises: a8e6f7b9c0d1
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b9f7e8a1c2d3"
down_revision: Union[str, None] = "a8e6f7b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("consent_withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "candidates",
        sa.Column(
            "withdrawn_from",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("candidates", "withdrawn_from")
    op.drop_column("candidates", "consent_withdrawn_at")
