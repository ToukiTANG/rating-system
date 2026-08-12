from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.common import ApiResponse


router = APIRouter(
    prefix="/health",
    tags=["System"],
)


class HealthData(BaseModel):
    status: Literal["ok"] = "ok"


@router.get(
    "",
    response_model=ApiResponse[HealthData],
)
async def health() -> ApiResponse[HealthData]:
    return ApiResponse(
        data=HealthData(),
    )