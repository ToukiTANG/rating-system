import base64
import hashlib
import hmac
import os
import uuid

from datetime import datetime, timezone
from email.utils import format_datetime
from io import BytesIO

import httpx
from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.exceptions import BusinessException


class UpyunService:
    """
    又拍云文件上传服务。

    当前负责：
    - RatingItem 图片校验
    - 图片压缩
    - 图片格式统一转换为 WebP
    - 上传到又拍云
    """

    # 原始上传文件最大大小：5 MB。
    MAX_IMAGE_SIZE = 5 * 1024 * 1024

    # 最终上传到又拍云的图片最大大小：500 KB。
    MAX_OUTPUT_IMAGE_SIZE = 500 * 1024

    # 图片最长边最大尺寸。
    MAX_IMAGE_DIMENSION = 1920

    # 最大允许像素数量。
    #
    # 防止尺寸异常大的压缩图片导致后端消耗大量内存。
    MAX_IMAGE_PIXELS = 40_000_000

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

        流程：
        1. 读取原始图片；
        2. 校验原始文件大小；
        3. 校验真实图片格式；
        4. 压缩并统一转换为 WebP；
        5. 确保最终图片不超过 500 KB；
        6. 上传又拍云；
        7. 返回 CDN URL。
        """

        content = await file.read()

        # =========================
        # 原始文件校验
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
                message="原始图片大小不能超过 5 MB",
                status_code=400,
            )

        # =========================
        # 图片处理
        # =========================

        content = self._process_image(
            content
        )

        # 图片经过后端处理后统一为 WebP。
        extension = "webp"

        content_type = "image/webp"

        # =========================
        # 生成云端文件路径
        # =========================

        now = datetime.now(
            timezone.utc
        )

        filename = (
            f"{uuid.uuid4().hex}"
            f".{extension}"
        )

        object_path = (
            f"/rating/"
            f"{now.year:04d}/"
            f"{now.month:02d}/"
            f"{filename}"
        )

        # 又拍云 REST API URI 必须包含 bucket。
        uri = (
            f"/{self.bucket}"
            f"{object_path}"
        )

        # =========================
        # 生成请求签名
        # =========================

        # 注意：
        # MD5 必须使用最终真正上传的压缩后图片内容。
        content_md5 = hashlib.md5(
            content
        ).hexdigest()

        date = format_datetime(
            datetime.now(
                timezone.utc
            ),
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
            response_text = (
                exc.response.text
            )

            print(
                "UPYUN upload failed:",
                exc.response.status_code,
                response_text,
            )

            raise BusinessException(
                code=12004,
                message=(
                    "图片上传又拍云失败，"
                    f"HTTP "
                    f"{exc.response.status_code}，"
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

    def _process_image(
        self,
        content: bytes,
    ) -> bytes:
        """
        校验并压缩图片。

        处理规则：
        - 仅允许 JPEG / PNG / WEBP；
        - 修正 EXIF 方向；
        - 最长边限制到 1920 px；
        - 统一输出 WebP；
        - 优先降低 WebP quality；
        - 如果仍超过 500 KB，则继续缩小分辨率；
        - 最终保证文件大小 <= 500 KB。
        """

        try:
            image = Image.open(
                BytesIO(content)
            )

            # =========================
            # 校验真实图片格式
            # =========================

            image_format = (
                image.format.upper()
                if image.format
                else ""
            )

            if image_format not in {
                "JPEG",
                "PNG",
                "WEBP",
            }:
                raise BusinessException(
                    code=12003,
                    message=(
                        "仅支持 JPEG、"
                        "PNG、WEBP 图片"
                    ),
                    status_code=400,
                )

            # =========================
            # 限制异常超大图片
            # =========================

            pixel_count = (
                image.width
                * image.height
            )

            if (
                pixel_count
                > self.MAX_IMAGE_PIXELS
            ):
                raise BusinessException(
                    code=12007,
                    message=(
                        "图片分辨率过高，"
                        "请上传较小的图片"
                    ),
                    status_code=400,
                )

            # 强制完整解码。
            #
            # 避免只有文件头合法，
            # 实际图片数据损坏。
            image.load()

            # =========================
            # 修正 EXIF 方向
            # =========================

            image = (
                ImageOps.exif_transpose(
                    image
                )
            )

            # =========================
            # 转换颜色模式
            # =========================

            # PNG / WebP 可能具有透明通道。
            if (
                image.mode == "RGBA"
                or image.mode == "LA"
                or (
                    image.mode == "P"
                    and "transparency"
                    in image.info
                )
            ):
                image = image.convert(
                    "RGBA"
                )

            else:
                image = image.convert(
                    "RGB"
                )

        except BusinessException:
            raise

        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ) as exc:
            raise BusinessException(
                code=12003,
                message="上传文件不是有效图片",
                status_code=400,
            ) from exc

        # =========================
        # 限制初始分辨率
        # =========================

        image.thumbnail(
            (
                self.MAX_IMAGE_DIMENSION,
                self.MAX_IMAGE_DIMENSION,
            ),
            Image.Resampling.LANCZOS,
        )

        current_image = image

        # =========================
        # 动态压缩
        # =========================

        while True:
            # ---------------------------------
            # 第一阶段：
            # 保持当前分辨率，
            # 从高质量逐步降低 WebP quality。
            # ---------------------------------

            for quality in range(
                85,
                39,
                -5,
            ):
                output = BytesIO()

                current_image.save(
                    output,
                    format="WEBP",
                    quality=quality,
                    method=6,
                )

                result = (
                    output.getvalue()
                )

                if (
                    len(result)
                    <= self.MAX_OUTPUT_IMAGE_SIZE
                ):
                    return result

            # ---------------------------------
            # 当前分辨率即使 quality=40
            # 仍然超过 500 KB。
            #
            # 继续缩小图片尺寸。
            # ---------------------------------

            width, height = (
                current_image.size
            )

            new_width = max(
                1,
                int(width * 0.85),
            )

            new_height = max(
                1,
                int(height * 0.85),
            )

            # 已经非常小仍然无法压缩到目标大小，
            # 不再继续循环。
            if (
                new_width < 256
                or new_height < 256
            ):
                output = BytesIO()

                current_image.save(
                    output,
                    format="WEBP",
                    quality=30,
                    method=6,
                )

                result = (
                    output.getvalue()
                )

                if (
                    len(result)
                    > self.MAX_OUTPUT_IMAGE_SIZE
                ):
                    raise BusinessException(
                        code=12006,
                        message=(
                            "图片压缩后"
                            "仍超过 500 KB"
                        ),
                        status_code=400,
                    )

                return result

            current_image = (
                current_image.resize(
                    (
                        new_width,
                        new_height,
                    ),
                    Image.Resampling.LANCZOS,
                )
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

        signature = (
            base64.b64encode(
                digest
            ).decode(
                "utf-8"
            )
        )

        return (
            f"UPYUN "
            f"{self.operator}:"
            f"{signature}"
        )