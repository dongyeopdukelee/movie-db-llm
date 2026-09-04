"""allow raw movie genres

Revision ID: d9bc4b1f2e03
Revises: cefd1f4875a6
Create Date: 2026-09-04 10:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9bc4b1f2e03"
down_revision: str | Sequence[str] | None = "cefd1f4875a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def legacy_genre_type() -> sa.Enum:
    """Return the constrained genre type used by the initial schema."""
    return sa.Enum(
        "action",
        "adventure",
        "animation",
        "comedy",
        "documentary",
        "drama",
        "fantasy",
        "horror",
        "romance",
        "thriller",
        name="genre",
        native_enum=False,
        create_constraint=True,
    )


def upgrade() -> None:
    """Replace the legacy genre check constraint with unrestricted text."""
    with op.batch_alter_table("movie_genres") as batch_op:
        batch_op.drop_constraint("genre", type_="check")
        batch_op.alter_column(
            "genre",
            existing_type=legacy_genre_type(),
            type_=sa.Text(),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Restore the initial fixed genre constraint for compatible data only."""
    with op.batch_alter_table("movie_genres") as batch_op:
        batch_op.alter_column(
            "genre",
            existing_type=sa.Text(),
            type_=legacy_genre_type(),
            existing_nullable=False,
        )
