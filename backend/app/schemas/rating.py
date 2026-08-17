from datetime import datetime
from enum import IntEnum
from typing import Generic, TypeVar, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator, model_validator,
)


class RatingStatus(IntEnum):
    """评分状态。"""

    INITIALIZED = 0
    RATING = 1
    RATED = 2


class CreateRatingItemRequest(BaseModel):
    """新增评分项目请求。"""

    name: str = Field(
        min_length=1,
        max_length=50,
        description="项目名称",
    )

    description: str = Field(
        default="",
        max_length=500,
        description="项目描述",
    )

    distinguish_expert: bool = Field(
        default=False,
        alias="distinguishExpert",
        description="是否区分专家评委",
    )

    expert_weight: float | None = Field(
        default=None,
        alias="expertWeight",
        gt=0,
        lt=1,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """去除名称首尾空格并检查空字符串。"""

        value = value.strip()

        if not value:
            raise ValueError("项目名称不能为空")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        """统一去除描述首尾空格。"""

        return value.strip()

    @model_validator(mode="after")
    def validate_expert_weight(self) -> Self:
        """
        校验专家评分配置。
        """

        if self.distinguish_expert:
            if self.expert_weight is None:
                raise ValueError(
                    "区分专家评委时必须设置专家评分占比"
                )
        else:
            # 不区分专家时清空专家权重。
            self.expert_weight = None

        return self


class RatingItemResponse(BaseModel):
    """评分项目响应。"""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int
    name: str
    description: str
    status: RatingStatus
    distinguish_expert: bool = Field(
        alias="distinguishExpert",
    )

    expert_weight: float | None = Field(
        alias="expertWeight",
    )

    expert_token: str | None = Field(
        default=None,
        alias="expertToken",
    )

    create_time: datetime = Field(
        alias="createTime",
    )

    update_time: datetime = Field(
        alias="updateTime",
    )


class UpdateRatingItemRequest(BaseModel):
    """
    修改评分项目请求。
    """

    # 需要修改的评分项目 ID。
    id: int = Field(
        ge=1,
        description="评分项目 ID",
    )

    # 项目名称。
    name: str = Field(
        min_length=1,
        max_length=50,
        description="项目名称",
    )

    # 项目描述。
    description: str = Field(
        default="",
        max_length=500,
        description="项目描述",
    )

    distinguish_expert: bool = Field(
        alias="distinguishExpert",
        description="是否区分专家评委",
    )

    expert_weight: float | None = Field(
        default=None,
        alias="expertWeight",
        gt=0,
        lt=1,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        去除项目名称首尾空格，
        并禁止名称仅包含空白字符。
        """

        value = value.strip()

        if not value:
            raise ValueError("项目名称不能为空")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
            cls,
            value: str,
    ) -> str:
        """
        去除项目描述首尾空格。
        """

        return value.strip()

    @model_validator(mode="after")
    def validate_expert_weight(self) -> Self:
        if self.distinguish_expert:
            if self.expert_weight is None:
                raise ValueError(
                    "区分专家评委时必须设置专家评分占比"
                )
        else:
            self.expert_weight = None

        return self


class DeleteRatingItemRequest(BaseModel):
    """
    删除评分项目请求。
    """

    # 待删除的评分项目 ID。
    id: int = Field(
        ge=1,
        description="评分项目 ID",
    )


class GetRatingItemRequest(BaseModel):
    """
    查询单个评分项目请求。
    """

    id: int = Field(
        ge=1,
        description="评分项目 ID",
    )


T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    """通用分页响应。"""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    list: list[T]

    total: int

    page: int

    page_size: int = Field(
        alias="pageSize",
    )


class RatingActionRequest(BaseModel):
    """
    评分项目操作请求。
    """

    id: int = Field(
        ge=1,
        description="评分项目 ID",
    )


class SubmitScoreRequest(BaseModel):
    """
    提交评分请求。
    """

    rating_item_id: int = Field(
        alias="ratingItemId",
        ge=1,
        description="评分项目 ID",
    )

    client_id: str = Field(
        alias="clientId",
        min_length=1,
        max_length=64,
        description="浏览器客户端唯一标识",
    )

    # 大众评分不传。
    #
    # 专家评分从专家二维码 URL 中获取。
    expert_token: str | None = Field(
        default=None,
        alias="expertToken",
        max_length=64,
    )

    score: float = Field(
        ge=0,
        le=5,
        description="评分",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class RatingStatusResponse(BaseModel):
    """
    当前客户端评分状态。
    """

    submitted: bool = Field(
        description="是否已经提交评分",
    )

    score: float | None = Field(
        default=None,
        description="已提交的评分",
    )

    submit_time: datetime | None = Field(
        default=None,
        alias="submitTime",
        description="提交时间",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class RatingStatisticsResponse(BaseModel):
    """
    评分项目统计结果。
    """

    average_score: float | None = Field(
        default=None,
        alias="averageScore",
        description="当前平均分",
    )

    rating_count: int = Field(
        default=0,
        alias="ratingCount",
        description="已提交评分数量",
    )

    update_time: datetime | None = Field(
        default=None,
        alias="updateTime",
        description="最后一条评分提交时间",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class RatingResultResponse(BaseModel):
    """
    评分结果响应。
    """

    id: int

    rating_item_id: int = Field(
        alias="ratingItemId",
    )

    score: float

    create_time: datetime = Field(
        alias="createTime",
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class RatingResultListItemResponse(BaseModel):
    """
    评分结果列表项。
    """

    # 评分结果 ID。
    id: int

    # 评分项目 ID。
    rating_item_id: int = Field(
        alias="ratingItemId",
    )

    # 评分项目名称。
    rating_item_name: str = Field(
        alias="ratingItemName",
    )

    # 客户端 ID。
    client_id: str = Field(
        alias="clientId",
    )

    # 评委类型：
    # 0 = 大众
    # 1 = 专家
    reviewer_type: int = Field(
        alias="reviewerType",
    )

    # 分数。
    score: float

    # 提交时间。
    create_time: datetime = Field(
        alias="createTime",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )
