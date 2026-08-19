from typing import Annotated

from fastapi import APIRouter, Query

from app.database.session import SessionDep
from app.schemas.common import ApiResponse, PageResult
from app.schemas.rating import (
    CreateRatingTopicRequest,
    DeleteRatingTopicRequest,
    RatingTopicEntryResponse,
    RatingTopicResponse,
    UpdateRatingTopicRequest, RatingTopicStatisticsResponse,
)
from app.services.rating_topic_service import RatingTopicService

router = APIRouter(
    prefix="/ratingTopic",
    tags=["RatingTopic"],
)


# =========================================================
# 查询评分主题列表
# =========================================================


@router.get(
    path="/query",
    response_model=ApiResponse[
        PageResult[RatingTopicResponse]
    ],
)
def query_rating_topic(
        db: SessionDep,
        name: Annotated[
            str | None,
            Query(
                max_length=50,
                description="评分主题名称",
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
    PageResult[RatingTopicResponse]
]:
    """
    分页查询评分主题。
    """

    service = RatingTopicService(db)

    result = service.list_topics(
        name=name,
        page=page,
        page_size=page_size,
    )

    return ApiResponse(
        data=result,
    )


# =========================================================
# 获取评分主题详情
# =========================================================


@router.get(
    path="/get",
    response_model=ApiResponse[
        RatingTopicResponse
    ],
)
def get_rating_topic(
        db: SessionDep,
        topic_id: Annotated[
            int,
            Query(
                alias="id",
                ge=1,
                description="评分主题 ID",
            ),
        ],
) -> ApiResponse[
    RatingTopicResponse
]:
    """
    获取评分主题详情。
    """

    service = RatingTopicService(db)

    result = service.get_topic(
        topic_id=topic_id,
    )

    return ApiResponse(
        data=result,
    )


# =========================================================
# 新增评分主题
# =========================================================


@router.post(
    path="/add",
    response_model=ApiResponse[
        RatingTopicResponse
    ],
)
def add_rating_topic(
        request: CreateRatingTopicRequest,
        db: SessionDep,
) -> ApiResponse[
    RatingTopicResponse
]:
    """
    新增评分主题。
    """

    service = RatingTopicService(db)

    result = service.create_topic(
        request
    )

    return ApiResponse(
        message="新增成功",
        data=result,
    )


# =========================================================
# 修改评分主题
# =========================================================


@router.post(
    path="/update",
    response_model=ApiResponse[
        RatingTopicResponse
    ],
)
def update_rating_topic(
        request: UpdateRatingTopicRequest,
        db: SessionDep,
) -> ApiResponse[
    RatingTopicResponse
]:
    """
    修改评分主题。
    """

    service = RatingTopicService(db)

    result = service.update_topic(
        request
    )

    return ApiResponse(
        message="修改成功",
        data=result,
    )


# =========================================================
# 删除评分主题
# =========================================================


@router.post(
    path="/delete",
    response_model=ApiResponse[bool],
)
def delete_rating_topic(
        request: DeleteRatingTopicRequest,
        db: SessionDep,
) -> ApiResponse[bool]:
    """
    删除评分主题。
    """

    service = RatingTopicService(db)

    service.delete_topic(
        topic_id=request.id,
    )

    return ApiResponse(
        message="删除成功",
        data=True,
    )


# =========================================================
# 获取当前评分入口
# =========================================================


@router.get(
    path="/entry",
    response_model=ApiResponse[
        RatingTopicEntryResponse
    ],
)
def get_rating_entry(
        db: SessionDep,
        topic_id: Annotated[
            int,
            Query(
                alias="topicId",
                ge=1,
                description="评分主题 ID",
            ),
        ],
        client_id: Annotated[
            str,
            Query(
                alias="clientId",
                min_length=1,
                max_length=64,
                description="客户端唯一标识",
            ),
        ],
        expert_token: Annotated[
            str | None,
            Query(
                alias="expertToken",
                min_length=1,
                description="专家评分凭证",
            ),
        ] = None,
) -> ApiResponse[
    RatingTopicEntryResponse
]:
    """
    获取评分主题当前评分入口。

    系统自动查找该 Topic 下当前正在评分的 RatingItem。

    不携带 expertToken：
        以大众评委身份进入。

    携带并通过 expertToken 校验：
        以专家评委身份进入。

    当存在正在评分的 RatingItem 时，
    根据当前评委类型申请该 Item 的评分名额。
    """

    service = RatingTopicService(db)

    result = service.get_rating_entry(
        topic_id=topic_id,
        client_id=client_id,
        expert_token=expert_token,
    )

    return ApiResponse(
        data=result,
    )


# =========================================================
# 获取评分主题统计
# =========================================================


@router.get(
    path="/statistics",
    response_model=ApiResponse[
        RatingTopicStatisticsResponse
    ],
)
def get_rating_topic_statistics(
        db: SessionDep,
        topic_id: Annotated[
            int,
            Query(
                alias="topicId",
                ge=1,
                description="评分主题 ID",
            ),
        ],
) -> ApiResponse[
    RatingTopicStatisticsResponse
]:
    """
    获取指定 Topic 下所有 RatingItem 的当前评分统计。

    返回结果按照最终得分从高到低排列，
    暂无评分数据的 RatingItem 排在最后。
    """

    service = RatingTopicService(db)

    result = service.get_statistics(
        topic_id=topic_id,
    )

    return ApiResponse(
        data=result,
    )
