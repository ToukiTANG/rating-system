#### 模型及数据库更新
+ 项目初始化时，应执行以下命令以让`alembic`接管数据库版本
```shell
uv run alembic upgrade head
```

+ 当新增实体类时，应在`models`文件下新建实体类，并在`app/models/__init__.py`文件中导入

+ 当`models`中的实体类变化时，应执行以下命令以更新数据库
```shell
uv run alembic revision --autogenerate -m "备注信息"
uv run alembic upgrade head
```