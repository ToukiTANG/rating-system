# Python 3.12 运行环境
FROM python:3.12-slim

# 从 uv 官方镜像复制 uv
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

# 工作目录
WORKDIR /app

# 国内服务器使用 PyPI 镜像，加速 Python 依赖下载
ENV UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple

# 先复制依赖文件，充分利用 Docker 缓存
COPY pyproject.toml uv.lock ./

# 安装生产依赖
RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-project

# 再复制后端代码
COPY . .

# 安装当前项目
RUN uv sync \
    --frozen \
    --no-dev

# FastAPI 服务端口
EXPOSE 8000

# 启动 FastAPI
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]