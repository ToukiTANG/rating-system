"""make rating item name unique within topic

Revision ID: 19ea5023f8c1
Revises: 17d449f16bc0
Create Date: 2026-08-18 14:38:17.457434

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "19ea5023f8c1"
down_revision: Union[str, Sequence[str], None] = "17d449f16bc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table(
        "rating_item",
        schema=None,
    ) as batch_op:
        # 原来的 name 使用 unique=True + index=True，
        # 因此数据库中实际是唯一索引，而不是 UniqueConstraint。
        batch_op.drop_index(
            "ix_rating_item_name",
        )

        # name 仍然保留普通索引能力。
        batch_op.create_index(
            "ix_rating_item_name",
            ["name"],
            unique=False,
        )

        # 唯一性调整为：
        # 同一个 Topic 内 RatingItem 名称不能重复。
        batch_op.create_unique_constraint(
            "uq_rating_item_topic_name",
            ["topic_id", "name"],
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table(
        "rating_item",
        schema=None,
    ) as batch_op:
        # 删除 Topic 内名称唯一约束。
        batch_op.drop_constraint(
            "uq_rating_item_topic_name",
            type_="unique",
        )

        # 删除当前普通 name 索引。
        batch_op.drop_index(
            "ix_rating_item_name",
        )

        # 恢复旧结构：
        # name 全局唯一，同时具有索引。
        batch_op.create_index(
            "ix_rating_item_name",
            ["name"],
            unique=True,
        )