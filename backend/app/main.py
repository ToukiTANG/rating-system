from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例。
    """

    app = FastAPI(
        title=settings.app_name,
        description="Rating System Backend API",
        version="0.1.0",
    )

    # -------------------------
    # CORS
    # -------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------
    # 注册全局异常处理
    # -------------------------

    register_exception_handlers(app)

    # -------------------------
    # 注册 API Router
    # -------------------------

    app.include_router(api_router)

    return app


app = create_app()