from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Rating System API",
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
    # 全局异常
    # -------------------------

    register_exception_handlers(app)

    # -------------------------
    # API Router
    # -------------------------

    app.include_router(api_router)

    return app


app = create_app()
