# app/models/rating_result.py

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class RatingResultModel(Base):
    """
    评分结果。

    同一个浏览器客户端，对同一个评分项目
    只能成功提交一次评分。
    """

    __tablename__ = "rating_result"

    __table_args__ = (
        UniqueConstraint(
            "rating_item_id",
            "client_id",
            name="uq_rating_result_item_client",
        ),
    )

    # 技术主键。
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 所属评分项目。
    rating_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "rating_item.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # 浏览器客户端标识。
    client_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # 用户评分。
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # 提交时间。
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )