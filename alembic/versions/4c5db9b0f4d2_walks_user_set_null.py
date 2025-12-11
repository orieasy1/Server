"""Set walks.user_id to ON DELETE SET NULL

Revision ID: 4c5db9b0f4d2
Revises: b862b8b9d5ac
Create Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4c5db9b0f4d2"
down_revision: Union[str, None] = "b862b8b9d5ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 FK 제거 (MySQL 기본 이름 추정: walks_ibfk_2)
    op.drop_constraint(
        "walks_ibfk_2",
        "walks",
        type_="foreignkey",
    )

    # 컬럼 NULL 허용
    op.alter_column(
        "walks",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # ON DELETE SET NULL 로 재생성
    op.create_foreign_key(
        "fk_walks_user_id_users",
        "walks",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 새 FK 제거
    op.drop_constraint(
        "fk_walks_user_id_users",
        "walks",
        type_="foreignkey",
    )

    # 원래 제약 재생성 (ON DELETE 없음 -> RESTRICT, NOT NULL)
    op.alter_column(
        "walks",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "walks_ibfk_2",
        "walks",
        "users",
        ["user_id"],
        ["user_id"],
    )
