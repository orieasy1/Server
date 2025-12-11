"""merge heads

Revision ID: 8346a0cf5844
Revises: 7c3f5b4f5c6a, cc21dfa763fc
Create Date: 2025-12-11 14:04:49.051209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8346a0cf5844'
down_revision: Union[str, None] = ('7c3f5b4f5c6a', 'cc21dfa763fc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
