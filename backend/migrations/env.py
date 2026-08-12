from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.database.base import Base

# 必须导入所有 ORM Model，
# 确保对应的 Table 已经注册到 Base.metadata。
import app.models  # noqa: F401


# Alembic 配置对象。
config = context.config


# 如果存在 alembic.ini，则使用其中的日志配置。
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Alembic autogenerate 会使用此 metadata
# 与当前数据库结构进行比较。
target_metadata = Base.metadata


def is_sqlite() -> bool:
    """
    判断当前数据库是否为 SQLite。

    SQLite 对 ALTER TABLE 的支持相对有限，
    因此迁移时启用 Alembic batch mode。
    """
    return settings.database_url.startswith("sqlite")


def run_migrations_offline() -> None:
    """
    离线模式执行数据库迁移。

    离线模式不会真正建立数据库连接，
    而是生成需要执行的 SQL。
    """

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },

        # SQLite 后续修改字段、约束时，
        # 使用 batch migration 能提高兼容性。
        render_as_batch=is_sqlite(),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式执行数据库迁移。

    这是开发和部署阶段最常用的模式：
    Alembic 会直接连接数据库并执行 migration。
    """

    engine = create_engine(
        settings.database_url,

        # Alembic 执行迁移时不需要长期维护连接池。
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,

            # SQLite 的 ALTER TABLE 功能有限。
            # Alembic batch mode 会在必要时通过
            # “创建临时表 -> 复制数据 -> 替换旧表”
            # 的方式完成结构迁移。
            render_as_batch=is_sqlite(),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()