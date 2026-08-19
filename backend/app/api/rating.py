from typing import Annotated

from fastapi import APIRouter, Query, status

from app.database.session import SessionDep
from app.schemas.common import ApiResponse
from app.schemas.rating import (
    CreateRatingItemRequest,
    RatingItemResponse,
    RatingStatus,
    UpdateRatingItemRequest,
    DeleteRatingItemRequest,
    RatingActionRequest,
    RatingStatisticsResponse,
    RatingResultResponse,
    SubmitScoreRequest,
    RatingStatusResponse, RatingResultListItemResponse
)
from app.services.rating_service import RatingService
from app.schemas.common import PageResult

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

        topic_id: Annotated[
            int | None,
            Query(
                alias="topicId",
                ge=1,
                description="评分主题 ID",
            ),
        ] = None,

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
        topic_id=topic_id,
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


@router.get(
    "/getItem",
    response_model=ApiResponse[
        RatingItemResponse
    ],
)
def get_rating_item(
        id: Annotated[
            int,
            Query(
                ge=1,
                description="评分项目 ID",
            ),
        ],
        db: SessionDep,
) -> ApiResponse[RatingItemResponse]:
    """
    查询单个评分项目。
    """

    service = RatingService(db)

    item = service.get_item(
        item_id=id,
    )

    return ApiResponse(
        data=item,
    )


@router.post(
    "/startRating",
    response_model=ApiResponse[
        RatingItemResponse
    ],
)
def start_rating(
        request: RatingActionRequest,
        db: SessionDep,
) -> ApiResponse[RatingItemResponse]:
    """
    开始评分。
    """

    service = RatingService(db)

    item = service.start_rating(
        item_id=request.id,
    )

    return ApiResponse(
        message="评分已开始",
        data=item,
    )


@router.post(
    "/finishRating",
    response_model=ApiResponse[
        RatingItemResponse
    ],
)
def finish_rating(
        request: RatingActionRequest,
        db: SessionDep,
) -> ApiResponse[RatingItemResponse]:
    """
    结束评分。
    """

    service = RatingService(db)

    item = service.finish_rating(
        item_id=request.id,
    )

    return ApiResponse(
        message="评分已结束",
        data=item,
    )


@router.get(
    "/getStatistics",
    response_model=ApiResponse[
        RatingStatisticsResponse
    ],
)
def get_statistics(
        db: SessionDep,
        id: int = Query(
            ge=1,
            description="评分项目 ID",
        ),
) -> ApiResponse[
    RatingStatisticsResponse
]:
    """
    获取评分项目实时统计结果。
    """

    service = RatingService(db)

    result = service.get_statistics(
        item_id=id,
    )

    return ApiResponse(
        data=result,
    )


@router.post(
    "/submitScore",
    response_model=ApiResponse[
        RatingResultResponse
    ],
)
def submit_score(
        request: SubmitScoreRequest,
        db: SessionDep,
) -> ApiResponse[RatingResultResponse]:
    """
    提交评分。
    """

    service = RatingService(db)

    result = service.submit_score(
        request=request,
    )

    return ApiResponse(
        message="评分提交成功",
        data=result,
    )


@router.get(
    "/getRatingStatus",
    response_model=ApiResponse[
        RatingStatusResponse
    ],
)
def get_rating_status(
        db: SessionDep,
        ratingItemId: int = Query(
            ge=1,
            description="评分项目 ID",
        ),
        clientId: str = Query(
            min_length=1,
            max_length=64,
            description="浏览器客户端 ID",
        ),
) -> ApiResponse[RatingStatusResponse]:
    """
    查询当前浏览器客户端的评分状态。
    """

    service = RatingService(db)

    result = service.get_rating_status(
        item_id=ratingItemId,
        client_id=clientId,
    )

    return ApiResponse(
        data=result,
    )


@router.get(
    "/queryResults",
    response_model=ApiResponse[
        PageResult[
            RatingResultListItemResponse
        ]
    ],
)
def query_results(
        db: SessionDep,
        page: int = Query(
            default=1,
            ge=1,
        ),
        pageSize: int = Query(
            default=10,
            ge=1,
            le=100,
        ),
        topicId: int | None = Query(
            default=None,
        ),
        itemName: str | None = Query(
            default=None,
        ),
        reviewerType: int | None = Query(
            default=None,
            ge=0,
            le=1,
        ),
        score: float | None = Query(
            default=None,
            ge=0,
            le=100,
        ),
):
    """
    分页查询评分结果。
    """

    service = RatingService(db)

    result = service.query_results(
        page=page,
        page_size=pageSize,
        topic_id=topicId,
        item_name=itemName,
        reviewer_type=reviewerType,
        score=score,
    )

    return ApiResponse(
        data=result,
    )
