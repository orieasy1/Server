"""Set notifications.target_user_id to ON DELETE SET NULL

Revision ID: 7c3f5b4f5c6a
Revises: 1b6d9e2e2ab8
Create Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7c3f5b4f5c6a"
down_revision: Union[str, None] = "1b6d9e2e2ab8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 FK 제거 (MySQL 기본 이름 추정)
    op.drop_constraint(
        "notifications_ibfk_4",
        "notifications",
        type_="foreignkey",
    )

    # 컬럼 NULL 허용
    op.alter_column(
        "notifications",
        "target_user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # ON DELETE SET NULL 로 재생성
    op.create_foreign_key(
        "fk_notifications_target_user_id_users",
        "notifications",
        "users",
        ["target_user_id"],
        ["user_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 새 FK 제거
    op.drop_constraint(
        "fk_notifications_target_user_id_users",
        "notifications",
        type_="foreignkey",
    )

    # 원래 제약 재생성 (ON DELETE 없음 -> RESTRICT)
    op.create_foreign_key(
        "notifications_ibfk_4",
        "notifications",
        "users",
        ["target_user_id"],
        ["user_id"],
    )
