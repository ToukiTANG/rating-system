from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, SmallInteger, String, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


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
    )

    # 主键，自增 ID。
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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

    # 是否区分专家评委。
    distinguish_expert: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # 专家评委占比。
    expert_weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
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