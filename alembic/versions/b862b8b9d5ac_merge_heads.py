"""merge heads

Revision ID: b862b8b9d5ac
Revises: 8346a0cf5844, 9d7be8c4c2f1
Create Date: 2025-12-11 14:10:10.522524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b862b8b9d5ac'
down_revision: Union[str, None] = ('8346a0cf5844', '9d7be8c4c2f1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
