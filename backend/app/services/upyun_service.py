import base64
import hashlib
import hmac
import os
import uuid

from datetime import datetime, timezone
from email.utils import format_datetime

import httpx
from fastapi import UploadFile

from app.core.exceptions import BusinessException


class UpyunService:
    """
    又拍云文件上传服务。

    当前仅负责 RatingItem 图片上传。
    """

    # 最大上传文件大小：5 MB。
    MAX_IMAGE_SIZE = 5 * 1024 * 1024

    # 又拍云 REST API 地址。
    API_BASE_URL = "https://v0.api.upyun.com"

    def __init__(self):
        self.bucket = os.getenv(
            "UPYUN_BUCKET",
            "",
        ).strip()

        self.operator = os.getenv(
            "UPYUN_OPERATOR",
            "",
        ).strip()

        self.password = os.getenv(
            "UPYUN_PASSWORD",
            "",
        )

        self.cdn_base_url = os.getenv(
            "UPYUN_CDN_BASE_URL",
            "",
        ).rstrip("/")

        if (
                not self.bucket
                or not self.operator
                or not self.password
                or not self.cdn_base_url
        ):
            raise RuntimeError(
                "又拍云配置不完整，请检查 "
                "UPYUN_BUCKET、UPYUN_OPERATOR、"
                "UPYUN_PASSWORD、UPYUN_CDN_BASE_URL"
            )

    async def upload_item_image(
            self,
            file: UploadFile,
    ) -> str:
        """
        上传 RatingItem 图片。

        返回上传完成后的 CDN URL。
        """

        content = await file.read()

        # =========================
        # 文件大小校验
        # =========================

        if not content:
            raise BusinessException(
                code=12001,
                message="上传图片不能为空",
                status_code=400,
            )

        if len(content) > self.MAX_IMAGE_SIZE:
            raise BusinessException(
                code=12002,
                message="图片大小不能超过 5 MB",
                status_code=400,
            )

        # =========================
        # 图片格式校验
        # =========================

        image_type = self._detect_image_type(
            content
        )

        if image_type is None:
            raise BusinessException(
                code=12003,
                message="仅支持 JPEG、PNG、WEBP 图片",
                status_code=400,
            )

        extension, content_type = image_type

        # =========================
        # 生成云端文件路径
        # =========================

        now = datetime.now(
            timezone.utc
        )

        filename = (
            f"{uuid.uuid4().hex}.{extension}"
        )

        object_path = (
            f"/rating/"
            f"{now.year:04d}/"
            f"{now.month:02d}/"
            f"{filename}"
        )

        # 又拍云 REST API URI 包含 bucket。
        uri = (
            f"/{self.bucket}"
            f"{object_path}"
        )

        # =========================
        # 生成请求签名
        # =========================

        content_md5 = hashlib.md5(
            content
        ).hexdigest()

        date = format_datetime(
            datetime.now(timezone.utc),
            usegmt=True,
        )

        authorization = (
            self._build_authorization(
                method="PUT",
                uri=uri,
                date=date,
                content_md5=content_md5,
            )
        )

        headers = {
            "Authorization": authorization,
            "Date": date,
            "Content-MD5": content_md5,
            "Content-Type": content_type,
            "Content-Length": str(
                len(content)
            ),
        }

        # =========================
        # 上传又拍云
        # =========================

        url = (
            f"{self.API_BASE_URL}"
            f"{uri}"
        )

        try:
            async with httpx.AsyncClient(
                    timeout=30.0,
            ) as client:
                response = await client.put(
                    url,
                    content=content,
                    headers=headers,
                )

                response.raise_for_status()


        except httpx.HTTPStatusError as exc:

            response_text = exc.response.text

            print(

                "UPYUN upload failed:",

                exc.response.status_code,

                response_text,

            )

            raise BusinessException(

                code=12004,

                message=(

                    "图片上传又拍云失败，"

                    f"HTTP {exc.response.status_code}，"

                    f"{response_text}"

                ),

                status_code=502,

            ) from exc

        except httpx.RequestError as exc:
            raise BusinessException(
                code=12005,
                message="连接又拍云失败",
                status_code=502,
            ) from exc

        # =========================
        # 返回 CDN URL
        # =========================

        return (
            f"{self.cdn_base_url}"
            f"{object_path}"
        )

    def _build_authorization(
            self,
            *,
            method: str,
            uri: str,
            date: str,
            content_md5: str,
    ) -> str:
        """
        根据又拍云 REST API 规则生成签名。
        """

        # 又拍云签名使用操作员密码的 MD5。
        password_md5 = hashlib.md5(
            self.password.encode(
                "utf-8"
            )
        ).hexdigest()

        sign_text = (
            f"{method}"
            f"&{uri}"
            f"&{date}"
            f"&{content_md5}"
        )

        digest = hmac.new(
            password_md5.encode(
                "utf-8"
            ),
            sign_text.encode(
                "utf-8"
            ),
            hashlib.sha1,
        ).digest()

        signature = base64.b64encode(
            digest
        ).decode("utf-8")

        return (
            f"UPYUN "
            f"{self.operator}:"
            f"{signature}"
        )

    @staticmethod
    def _detect_image_type(
            content: bytes,
    ) -> tuple[str, str] | None:
        """
        根据文件真实内容识别图片类型。

        不直接相信：
        - 文件扩展名
        - UploadFile.content_type

        当前允许：
        JPEG / PNG / WEBP
        """

        # JPEG
        if content.startswith(
                b"\xff\xd8\xff"
        ):
            return (
                "jpg",
                "image/jpeg",
            )

        # PNG
        if content.startswith(
                b"\x89PNG\r\n\x1a\n"
        ):
            return (
                "png",
                "image/png",
            )

        # WEBP
        if (
                len(content) >= 12
                and content[0:4] == b"RIFF"
                and content[8:12] == b"WEBP"
        ):
            return (
                "webp",
                "image/webp",
            )

        return None
