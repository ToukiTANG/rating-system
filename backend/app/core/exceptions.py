from typing import Any


class BusinessException(Exception):
    """业务异常。"""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        status_code: int = 400,
        data: Any = None,
    ) -> None:
        super().__init__(message)

        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data