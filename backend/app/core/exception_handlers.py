from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import BusinessException


def build_error_response(
        *,
        code: int,
        message: str,
        data: Any = None,
        status_code: int,
) -> JSONResponse:
    """
    构建统一异常响应。
    """

    content = {
        "code": code,
        "message": message,
        "data": data,
    }

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册全局异常处理器。
    """

    @app.exception_handler(BusinessException)
    async def business_exception_handler(
            _request: Request,
            exc: BusinessException,
    ) -> JSONResponse:
        return build_error_response(
            code=exc.code,
            message=exc.message,
            data=exc.data,
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
            _request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse:
        return build_error_response(
            code=40001,
            message="请求参数校验失败",
            data={
                "errors": exc.errors(),
            },
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
            _request: Request,
            exc: StarletteHTTPException,
    ) -> JSONResponse:
        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "HTTP 请求异常"
        )

        return build_error_response(
            code=exc.status_code * 100,
            message=message,
            data=None,
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(
            _request: Request,
            _exc: Exception,
    ) -> JSONResponse:
        return build_error_response(
            code=50000,
            message="服务器内部异常",
            data=None,
            status_code=500,
        )
