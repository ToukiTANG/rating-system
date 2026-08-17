# Python 3.12 运行环境
FROM python:3.12-slim

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

WORKDIR /app

# 先复制依赖定义文件
COPY pyproject.toml uv.lock ./

# 从 uv.lock 导出锁定版本的第三方依赖
RUN uv export \
    --frozen \
    --no-dev \
    --no-emit-project \
    --format requirements.txt \
    --output-file /tmp/requirements.txt

# 创建虚拟环境，并通过腾讯云 PyPI 镜像安装锁定依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    uv pip sync \
    --python /app/.venv/bin/python \
    --default-index https://mirrors.cloud.tencent.com/pypi/simple \
    /tmp/requirements.txt

# 最后复制项目代码
COPY . .

EXPOSE 8000

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]