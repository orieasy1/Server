"""Set photos.uploaded_by to ON DELETE SET NULL

Revision ID: 9d7be8c4c2f1
Revises: 7c3f5b4f5c6a
Create Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9d7be8c4c2f1"
down_revision: Union[str, None] = "7c3f5b4f5c6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 FK 제거 (MySQL 기본 이름 추정: photos_ibfk_1)
    op.drop_constraint(
        "photos_ibfk_1",
        "photos",
        type_="foreignkey",
    )

    # 컬럼 NULL 허용
    op.alter_column(
        "photos",
        "uploaded_by",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # ON DELETE SET NULL 로 재생성
    op.create_foreign_key(
        "fk_photos_uploaded_by_users",
        "photos",
        "users",
        ["uploaded_by"],
        ["user_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 새 FK 제거
    op.drop_constraint(
        "fk_photos_uploaded_by_users",
        "photos",
        type_="foreignkey",
    )

    # 원래 제약 재생성 (ON DELETE 없음 -> RESTRICT, NOT NULL)
    op.alter_column(
        "photos",
        "uploaded_by",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "photos_ibfk_1",
        "photos",
        "users",
        ["uploaded_by"],
        ["user_id"],
    )
