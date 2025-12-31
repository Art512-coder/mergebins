"""Update models to match database schema

Revision ID: 47231eccc790
Revises: e2d19f248c3f
Create Date: 2025-11-24 15:23:44.411711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47231eccc790'
down_revision: Union[str, None] = 'e2d19f248c3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
