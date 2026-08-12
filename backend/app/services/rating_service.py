from datetime import datetime

from app.core.exceptions import BusinessException
from app.schemas.rating import (
    CreateRatingItemRequest,
    PageResult,
    RatingItemResponse,
    RatingStatus,
)


class RatingService:
    """评分项目业务服务。"""

    def __init__(self) -> None:
        self._items: list[RatingItemResponse] = [
            RatingItemResponse(
                id=1,
                name="回答准确性",
                description="用于评估模型回答内容是否准确。",
                status=RatingStatus.INITIALIZED,
                create_time=datetime.now(),
                update_time=datetime.now(),
            ),
            RatingItemResponse(
                id=2,
                name="回答完整性",
                description="用于评估回答是否完整覆盖用户问题。",
                status=RatingStatus.RATING,
                create_time=datetime.now(),
                update_time=datetime.now(),
            ),
            RatingItemResponse(
                id=3,
                name="回答相关性",
                description="用于评估回答与用户问题之间的相关程度。",
                status=RatingStatus.RATED,
                create_time=datetime.now(),
                update_time=datetime.now(),
            ),
        ]

        self._next_id = 4

    def list_items(
        self,
        *,
        name: str | None,
        status: RatingStatus | None,
        page: int,
        page_size: int,
    ) -> PageResult[RatingItemResponse]:
        """
        查询评分项目列表。
        """

        items = self._items

        # 名称模糊搜索
        if name:
            keyword = name.strip().lower()

            items = [
                item
                for item in items
                if keyword in item.name.lower()
            ]

        # 状态过滤
        if status is not None:
            items = [
                item
                for item in items
                if item.status == status
            ]

        total = len(items)

        start = (page - 1) * page_size
        end = start + page_size

        page_items = items[start:end]

        return PageResult(
            list=page_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def create_item(
        self,
        request: CreateRatingItemRequest,
    ) -> RatingItemResponse:
        """
        创建评分项目。
        """

        # 名称唯一性校验
        normalized_name = request.name.strip().lower()

        exists = any(
            item.name.strip().lower() == normalized_name
            for item in self._items
        )

        if exists:
            raise BusinessException(
                code=10001,
                message="评分项目名称已存在",
                status_code=409,
            )

        now = datetime.now()

        item = RatingItemResponse(
            id=self._next_id,
            name=request.name,
            description=request.description,
            status=RatingStatus.INITIALIZED,
            create_time=now,
            update_time=now,
        )

        self._items.append(item)

        self._next_id += 1

        return item


rating_service = RatingService()