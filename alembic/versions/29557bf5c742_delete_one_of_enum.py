"""delete one of enum

Revision ID: 29557bf5c742
Revises: d2edb277ce13
Create Date: 2025-11-19 07:33:20.170532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29557bf5c742'
down_revision: Union[str, None] = 'd2edb277ce13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
