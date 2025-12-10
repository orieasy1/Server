"""add voice_url to pets

Revision ID: add_voice_url_pets
Revises: add_fcm_token_001
Create Date: 2025-12-10
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_voice_url_pets'
down_revision = 'add_fcm_token_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pets 테이블에 voice_url 컬럼 추가
    op.add_column('pets', sa.Column('voice_url', sa.String(255), nullable=True))


def downgrade() -> None:
    # voice_url 컬럼 삭제
    op.drop_column('pets', 'voice_url')

