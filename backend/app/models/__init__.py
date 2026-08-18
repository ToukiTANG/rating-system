"""
统一导入所有 ORM Model。

Alembic 在执行 autogenerate 时，需要所有 ORM Model
都已经被导入，从而注册到 Base.metadata 中。
"""

from app.models.rating_item import RatingItemModel
from app.models.rating_result import RatingResultModel
from app.models.rating_topic import RatingTopicModel
from app.models.rating_item_participant import RatingItemParticipantModel

__all__ = [
    "RatingItemModel",
    "RatingResultModel",
    "RatingTopicModel",
    "RatingItemParticipantModel"
]
