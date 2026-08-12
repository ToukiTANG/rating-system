from typing import Annotated

from fastapi import APIRouter, Query, status

from app.schemas.common import ApiResponse
from app.schemas.rating import (
    CreateRatingItemRequest,
    PageResult,
    RatingItemResponse,
    RatingStatus,
)
from app.services.rating_service import rating_service


router = APIRouter(
    prefix="/rating",
    tags=["Rating"],
)

@router.get(
    "/items",
    response_model=ApiResponse[PageResult[RatingItemResponse]],
)
async def get_rating_item_list(
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
) -> ApiResponse[PageResult[RatingItemResponse]]:
    result = rating_service.list_items(
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
    response_model=ApiResponse[RatingItemResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_rating_item(
    request: CreateRatingItemRequest,
) -> ApiResponse[RatingItemResponse]:
    item = rating_service.create_item(request)

    return ApiResponse(
        message="新增成功",
        data=item,
    )