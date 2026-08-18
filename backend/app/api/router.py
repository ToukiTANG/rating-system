from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.rating import router as rating_router
from app.api.rating_topic import router as rating_topic_router


api_router = APIRouter(
    prefix="/ratingSys",
)

api_router.include_router(health_router)
api_router.include_router(rating_router)
api_router.include_router(rating_topic_router)