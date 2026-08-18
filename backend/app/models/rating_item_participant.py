from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.rating_item import RatingItemModel


class RatingItemParticipantModel(Base):
    """
    RatingItem 评分参与者。

    用于记录某个客户端是否已经取得某个 RatingItem
    的评分资格，以及对应的评委类型。

    reviewer_type:
        0 = 大众评委
        1 = 专家评委
    """

    __tablename__ = "rating_item_participant"

    __table_args__ = (
        # 同一个客户端在同一个 RatingItem
        # 中只能占用一个评分名额。
        UniqueConstraint(
            "rating_item_id",
            "client_id",
            name="uq_rating_item_participant_item_client",
        ),

        # 用于快速统计某个 Item 下
        # 大众 / 专家已经占用的人数。
        Index(
            "ix_rating_item_participant_item_reviewer",
            "rating_item_id",
            "reviewer_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    rating_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "rating_item.id",
            name="fk_rating_item_participant_rating_item_id",
        ),
        nullable=False,
    )

    client_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    reviewer_type: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    item: Mapped["RatingItemModel"] = relationship(
        back_populates="participants",
    )
