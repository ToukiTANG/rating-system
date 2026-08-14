from typing import Annotated

from fastapi import APIRouter, Query, status

from app.database.session import SessionDep
from app.schemas.common import ApiResponse
from app.schemas.rating import (
    CreateRatingItemRequest,
    PageResult,
    RatingItemResponse,
    RatingStatus,
    UpdateRatingItemRequest,
    DeleteRatingItemRequest
)
from app.services.rating_service import RatingService

router = APIRouter(
    prefix="/rating",
    tags=["Rating"],
)


@router.get(
    "/items",
    response_model=ApiResponse[
        PageResult[RatingItemResponse]
    ],
)
def get_rating_item_list(
        db: SessionDep,

        name: Annotated[
            str | None,
            Query(
                max_length=50,
                description="项目名称",
            ),
        ] = None,

        status_: Annotated[
            RatingStatus | None,
            Query(
                alias="status",
                description="项目状态",
            ),
        ] = None,

        page: Annotated[
            int,
            Query(
                ge=1,
                description="页码",
            ),
        ] = 1,

        page_size: Annotated[
            int,
            Query(
                alias="pageSize",
                ge=1,
                le=100,
                description="每页数量",
            ),
        ] = 10,
) -> ApiResponse[
    PageResult[RatingItemResponse]
]:
    """
    分页查询评分项目。
    """

    service = RatingService(db)

    result = service.list_items(
        name=name,
        status=status_,
        page=page,
        page_size=page_size,
    )

    return ApiResponse(
        data=result,
    )


@router.post(
    "/addItem",
    response_model=ApiResponse[
        RatingItemResponse
    ],
    status_code=status.HTTP_201_CREATED,
)
def create_rating_item(
        request: CreateRatingItemRequest,
        db: SessionDep,
) -> ApiResponse[RatingItemResponse]:
    """
    新增评分项目。
    """

    service = RatingService(db)

    item = service.create_item(
        request
    )

    return ApiResponse(
        message="新增成功",
        data=item,
    )


@router.post(
    "/updateItem",
    response_model=ApiResponse[
        RatingItemResponse
    ],
)
def update_rating_item(
        request: UpdateRatingItemRequest,
        db: SessionDep,
) -> ApiResponse[RatingItemResponse]:
    """
    修改评分项目。
    """

    service = RatingService(db)

    item = service.update_item(
        request=request,
    )

    return ApiResponse(
        message="修改成功",
        data=item,
    )


@router.post(
    "/deleteItem",
    response_model=ApiResponse[bool],
)
def delete_rating_item(
        request: DeleteRatingItemRequest,
        db: SessionDep,
) -> ApiResponse[bool]:
    """
    删除评分项目。
    """

    service = RatingService(db)

    service.delete_item(
        request=request,
    )

    return ApiResponse(
        message="删除成功",
        data=True,
    )
