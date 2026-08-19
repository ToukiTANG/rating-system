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


class CreateRatingTopicRequest(BaseModel):
    """
    新增评分主题请求。
    """

    # 主题名称。
    name: str = Field(
        min_length=1,
        max_length=50,
        description="评分主题名称",
    )

    # 主题描述。
    description: str = Field(
        default="",
        max_length=500,
        description="评分主题描述",
    )

    # 是否区分专家评委。
    distinguish_expert: bool = Field(
        default=False,
        alias="distinguishExpert",
        description="是否区分专家评委",
    )

    # 专家评分占比。
    #
    # 例如：
    # 0.6 表示专家评分占最终评分的 60%。
    expert_weight: float | None = Field(
        default=None,
        alias="expertWeight",
        gt=0,
        lt=1,
        description="专家评分占比",
    )

    # 大众评分入口允许参与的评委人数上限。
    public_limit: int = Field(
        alias="publicLimit",
        ge=1,
        description="大众评委人数上限",
    )

    # 专家评分入口允许参与的评委人数上限。
    #
    # 不区分专家评分时为空。
    expert_limit: int | None = Field(
        default=None,
        alias="expertLimit",
        ge=1,
        description="专家评委人数上限",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        去除主题名称首尾空格，
        并禁止名称仅包含空白字符。
        """

        value = value.strip()

        if not value:
            raise ValueError("评分主题名称不能为空")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
            cls,
            value: str,
    ) -> str:
        """
        去除主题描述首尾空格。
        """

        return value.strip()

    @model_validator(mode="after")
    def validate_expert_config(self) -> Self:
        """
        校验专家评分相关配置。
        """

        if self.distinguish_expert:
            if self.expert_weight is None:
                raise ValueError(
                    "区分专家评委时必须设置专家评分占比"
                )

            if self.expert_limit is None:
                raise ValueError(
                    "区分专家评委时必须设置专家评委人数上限"
                )

        else:
            # 不区分专家评分时，
            # 专家相关配置统一清空。
            self.expert_weight = None
            self.expert_limit = None

        return self


class UpdateRatingTopicRequest(BaseModel):
    """
    修改评分主题。

    Topic 创建后：
    - 是否区分专家不可修改
    - 大众评委人数不可修改
    - 专家评委人数不可修改
    - 专家 Token 不可修改

    仅允许修改：
    - 名称
    - 描述
    - 专家评分占比
    """

    id: int = Field(
        ge=1,
        description="评分主题 ID",
    )

    name: str = Field(
        min_length=1,
        max_length=50,
        description="评分主题名称",
    )

    description: str = Field(
        default="",
        max_length=500,
        description="评分主题描述",
    )

    expert_weight: float | None = Field(
        default=None,
        alias="expertWeight",
        gt=0,
        lt=1,
        description="专家评分占比",
    )

    @field_validator("name")
    @classmethod
    def validate_name(
            cls,
            value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "评分主题名称不能为空"
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
            cls,
            value: str,
    ) -> str:
        return value.strip()

    model_config = ConfigDict(
        populate_by_name=True,
    )


class RatingTopicResponse(BaseModel):
    """
    评分主题响应。
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int

    name: str

    description: str

    distinguish_expert: bool = Field(
        alias="distinguishExpert",
    )

    expert_weight: float | None = Field(
        default=None,
        alias="expertWeight",
    )

    public_limit: int = Field(
        alias="publicLimit",
    )

    expert_limit: int | None = Field(
        default=None,
        alias="expertLimit",
    )

    # 专家二维码使用的凭证。
    #
    # 只返回给管理端。
    # 后续面向扫码用户的接口不会使用这个 Response，
    # 避免把专家 Token 暴露给大众评分页面。
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


class DeleteRatingTopicRequest(BaseModel):
    """
    删除评分主题请求。
    """

    id: int = Field(
        ge=1,
        description="评分主题 ID",
    )


class GetRatingTopicRequest(BaseModel):
    """
    查询单个评分主题请求。
    """

    id: int = Field(
        ge=1,
        description="评分主题 ID",
    )


class CreateRatingItemRequest(BaseModel):
    """新增评分项目请求。"""

    # 所属评分主题 ID。
    topic_id: int = Field(
        alias="topicId",
        ge=1,
        description="所属评分主题 ID",
    )

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

    image_url: str = Field(
        alias="imageUrl",
        min_length=1,
        max_length=500,
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


class RatingItemResponse(BaseModel):
    """
    评分项目响应。
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int

    # 所属评分主题。
    #
    # 当前仍允许为空，
    # 用于兼容历史 RatingItem 数据。
    topic_id: int | None = Field(
        default=None,
        alias="topicId",
    )

    name: str

    description: str

    image_url: str | None = Field(
        default=None,
        alias="imageUrl",
    )

    status: RatingStatus

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

    # 评分项目 ID。
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

    image_url: str | None = Field(
        default=None,
        alias="imageUrl",
        min_length=1,
        max_length=500,
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
        le=100,
        description="评分值：专家为 0~100 分，大众为 1 或 2 个赞",
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

    # 当前最终得分。
    #
    # 区分专家评委：
    #   专家平均分 × 专家权重
    #   +
    #   大众点赞总数 × 大众权重
    #
    # 不区分专家评委：
    #   大众点赞总数
    final_score: float = Field(
        default=0.0,
        alias="finalScore",
        description="当前最终得分",
    )

    # 已提交评分人数。
    rating_count: int = Field(
        default=0,
        alias="ratingCount",
        description="已提交评分数量",
    )

    # 最后一次评分提交时间。
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

    id: int

    topic_id: int | None = Field(
        default=None,
        alias="topicId",
    )

    topic_name: str | None = Field(
        default=None,
        alias="topicName",
    )

    rating_item_id: int = Field(
        alias="ratingItemId",
    )

    rating_item_name: str = Field(
        alias="ratingItemName",
    )

    client_id: str = Field(
        alias="clientId",
    )

    reviewer_type: int = Field(
        alias="reviewerType",
    )

    score: float

    create_time: datetime = Field(
        alias="createTime",
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TopicActiveRatingItemResponse(BaseModel):
    """
    Topic 当前正在评分的评分项目。
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int

    topic_id: int = Field(
        alias="topicId",
    )

    name: str

    description: str

    status: RatingStatus


class RatingTopicEntryResponse(BaseModel):
    """
    Topic 评分入口响应。

    扫描 Topic 二维码后，
    根据 Topic 自动获取当前正在评分的 RatingItem。
    """

    topic_id: int = Field(
        alias="topicId",
    )

    topic_name: str = Field(
        alias="topicName",
    )

    # 0 = 大众评委
    # 1 = 专家评委
    reviewer_type: int = Field(
        alias="reviewerType",
    )

    # 当前正在评分的项目。
    #
    # 没有评分中的项目时返回 null，
    # 这是正常业务状态，不作为异常处理。
    active_item: TopicActiveRatingItemResponse | None = Field(
        default=None,
        alias="activeItem",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )

class UploadItemImageResponse(
    BaseModel
):
    """
    RatingItem 图片上传响应。
    """

    url: str