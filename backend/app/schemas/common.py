from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应结构。"""

    code: int = 0
    message: str = "success"
    data: T | None = None



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
