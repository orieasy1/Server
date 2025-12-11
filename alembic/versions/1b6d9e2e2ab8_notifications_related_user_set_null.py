"""Set notifications.related_user_id to ON DELETE SET NULL

Revision ID: 1b6d9e2e2ab8
Revises: ac5ec9f45c08
Create Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1b6d9e2e2ab8"
down_revision: Union[str, None] = "ac5ec9f45c08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 FK 제거 (MySQL 기본 이름)
    op.drop_constraint(
        "notifications_ibfk_3",
        "notifications",
        type_="foreignkey",
    )

    # 컬럼 NULL 허용
    op.alter_column(
        "notifications",
        "related_user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # ON DELETE SET NULL 로 재생성
    op.create_foreign_key(
        "fk_notifications_related_user_id_users",
        "notifications",
        "users",
        ["related_user_id"],
        ["user_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 새 FK 제거
    op.drop_constraint(
        "fk_notifications_related_user_id_users",
        "notifications",
        type_="foreignkey",
    )

    # 원래 제약 재생성 (ON DELETE 없음 -> RESTRICT)
    op.create_foreign_key(
        "notifications_ibfk_3",
        "notifications",
        "users",
        ["related_user_id"],
        ["user_id"],
    )
