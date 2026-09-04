"""make release year optional

Revision ID: e47a38bf2c19
Revises: d9bc4b1f2e03
Create Date: 2026-09-04 11:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e47a38bf2c19"
down_revision: str | Sequence[str] | None = "d9bc4b1f2e03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow catalog movies to omit their release year."""
    with op.batch_alter_table("movies") as batch_op:
        batch_op.alter_column(
            "release_year",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    """Require release years again for compatible data only."""
    with op.batch_alter_table("movies") as batch_op:
        batch_op.alter_column(
            "release_year",
            existing_type=sa.Integer(),
            nullable=False,
        )
