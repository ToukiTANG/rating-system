from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。"""

    # 应用名称
    app_name: str = "Rating System API"

    # 当前运行环境
    environment: str = "development"

    # 数据库连接地址
    #
    # 开发阶段默认使用 SQLite。
    # 后续切换 MySQL / PostgreSQL 时只需要修改该配置。
    database_url: str = "sqlite:///./data/rating_system.db"

    model_config = SettingsConfigDict(
        # 自动读取 backend/.env 文件
        env_file=".env",
        env_file_encoding="utf-8",

        # 忽略 .env 中当前 Settings 未声明的其他配置
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    获取应用配置。

    使用缓存避免每次请求都重新读取 .env 文件。
    """
    return Settings()


settings = get_settings()