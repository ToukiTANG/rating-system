from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_connect_args() -> dict:
    """
    根据数据库类型生成额外连接参数。

    SQLite 默认限制连接只能在创建它的线程中使用。
    FastAPI 的同步接口可能在线程池中的不同线程执行，
    因此 SQLite 开发环境需要关闭该限制。
    """

    if settings.database_url.startswith("sqlite"):
        return {
            "check_same_thread": False,
        }

    return {}


# SQLAlchemy Engine。
#
# pool_pre_ping=True：
# 使用连接之前先检查连接是否仍然有效，
# 对 MySQL/PostgreSQL 等长连接场景也比较有用。
engine = create_engine(
    settings.database_url,
    connect_args=create_connect_args(),
    pool_pre_ping=True,
)


# Session 工厂。
SessionLocal = sessionmaker(
    bind=engine,

    # 不自动 flush，事务提交时再显式处理。
    autoflush=False,

    # commit 后保留 ORM 对象属性，
    # 避免返回响应时再次触发数据库查询。
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 数据库 Session 依赖。

    每个请求创建一个独立 Session。
    请求结束后无论成功或失败都会关闭 Session。
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# FastAPI Annotated 类型别名。
#
# 路由中可以直接写：
#
#     def xxx(db: SessionDep):
#
# 不需要每个接口重复 Depends(get_db)。
SessionDep = Annotated[Session, Depends(get_db)]