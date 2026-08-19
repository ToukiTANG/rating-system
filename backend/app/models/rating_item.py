from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.rating_topic import RatingTopicModel
    from app.models.rating_item_participant import (
        RatingItemParticipantModel,
    )


class RatingItemModel(Base):
    """
    评分项目数据库模型。
    """

    __tablename__ = "rating_item"

    # 数据库级约束：
    # status 只能是 0 / 1 / 2。
    __table_args__ = (
        CheckConstraint(
            "status IN (0, 1, 2)",
            name="ck_rating_item_status",
        ),

        UniqueConstraint(
            "topic_id",
            "name",
            name="uq_rating_item_topic_name",
        ),

        Index(
            "uq_rating_item_topic_active",
            "topic_id",
            unique=True,
            sqlite_where=text("status = 1"),
        ),
    )

    # 主键，自增 ID。
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 所属评分主题 ID。
    topic_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "rating_topic.id",
            name="fk_rating_item_topic_id_rating_topic",
        ),
        nullable=True,
        index=True,
    )

    # 所属评分主题。
    topic: Mapped["RatingTopicModel | None"] = relationship(
        back_populates="items",
    )

    # 项目名称。
    #
    # unique=True：
    # 数据库层面保证项目名称不能重复。
    #
    # index=True：
    # 后续按名称查询时可以使用索引。
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    # 项目描述。
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # 项目状态：
    #
    # 0：初始化
    # 1：评分中
    # 2：已评分
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        index=True,
    )

    # 创建时间。
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    # 更新时间。
    #
    # 当 SQLAlchemy 更新该记录时，
    # 自动更新 update_time。
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    participants: Mapped[
        list["RatingItemParticipantModel"]
    ] = relationship(
        back_populates="item",
    )
