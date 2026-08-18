from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.rating_item import RatingItemModel


class RatingTopicModel(Base):
    """
    评分主题数据库模型。

    一个评分主题下可以包含多个评分项目 RatingItem。
    评分规则、专家配置以及二维码使用限制统一归属于评分主题。
    """

    __tablename__ = "rating_topic"

    __table_args__ = (
        # 专家权重必须在 0 ~ 1 之间。
        CheckConstraint(
            "expert_weight IS NULL OR (expert_weight > 0 AND expert_weight < 1)",
            name="ck_rating_topic_expert_weight",
        ),

        # 大众评委人数上限必须大于 0。
        CheckConstraint(
            "public_limit > 0",
            name="ck_rating_topic_public_limit",
        ),

        # 专家评委人数上限为空，或者必须大于 0。
        CheckConstraint(
            "expert_limit IS NULL OR expert_limit > 0",
            name="ck_rating_topic_expert_limit",
        ),
    )

    # 主键，自增 ID。
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 评分主题名称。
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    # 评分主题描述。
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )

    # 是否区分专家评委。
    #
    # False：
    # 只生成大众评分二维码。
    #
    # True：
    # 同时生成大众评分二维码和专家评分二维码。
    distinguish_expert: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # 专家评分占比。
    #
    # 例如：
    # 0.6 表示专家评分占最终评分的 60%。
    #
    # 当 distinguish_expert = False 时为空。
    expert_weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # 大众评分二维码允许参与的评委人数上限。
    #
    # 注意：
    # 这里限制的是“不同评委的参与人数”，
    # 不是二维码被扫码或页面被刷新的次数。
    public_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # 专家评分二维码允许参与的评委人数上限。
    #
    # 当 distinguish_expert = False 时为空。
    expert_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # 专家评分入口凭证。
    #
    # 一个 RatingTopic 只生成一个专家评分 Token，
    # Topic 下所有 RatingItem 共用该专家评分入口。
    #
    # 当 distinguish_expert = False 时为空。
    expert_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # 创建时间。
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    # 更新时间。
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    # 主题下的评分项目。
    items: Mapped[list["RatingItemModel"]] = relationship(
        back_populates="topic",
    )
