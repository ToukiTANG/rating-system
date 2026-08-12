from datetime import datetime
from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
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
    """评分项目响应。"""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int
    name: str
    description: str
    status: RatingStatus

    create_time: datetime = Field(
        alias="createTime",
    )

    update_time: datetime = Field(
        alias="updateTime",
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