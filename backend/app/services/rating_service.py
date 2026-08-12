from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.rating_item import RatingItemModel
from app.schemas.rating import (
    CreateRatingItemRequest,
    PageResult,
    RatingItemResponse,
    RatingStatus,
    UpdateRatingItemRequest,
)


class RatingService:
    """
    评分项目业务服务。
    """

    def __init__(self, db: Session) -> None:
        # 当前请求对应的数据库 Session。
        self.db = db

    def list_items(
            self,
            *,
            name: str | None,
            status: RatingStatus | None,
            page: int,
            page_size: int,
    ) -> PageResult[RatingItemResponse]:
        """
        分页查询评分项目。
        """

        # -------------------------
        # 构建查询条件
        # -------------------------

        conditions = []

        if name:
            keyword = name.strip()

            if keyword:
                # 项目名称模糊查询。
                conditions.append(
                    RatingItemModel.name.ilike(
                        f"%{keyword}%"
                    )
                )

        if status is not None:
            # 注意：
            # status=0 是合法状态，
            # 因此不能写 if status。
            conditions.append(
                RatingItemModel.status == int(status)
            )

        # -------------------------
        # 查询总记录数
        # -------------------------

        count_stmt = select(
            func.count(RatingItemModel.id)
        )

        if conditions:
            count_stmt = count_stmt.where(
                *conditions
            )

        total = self.db.scalar(
            count_stmt
        ) or 0

        # -------------------------
        # 查询当前页数据
        # -------------------------

        stmt = select(
            RatingItemModel
        )

        if conditions:
            stmt = stmt.where(
                *conditions
            )

        # 默认按 ID 倒序，
        # 新创建的数据优先显示。
        stmt = (
            stmt
            .order_by(RatingItemModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = self.db.scalars(
            stmt
        ).all()

        # SQLAlchemy ORM Model
        # 转换为 Pydantic Response Model。
        response_items = [
            RatingItemResponse.model_validate(item)
            for item in items
        ]

        return PageResult(
            list=response_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def create_item(
            self,
            request: CreateRatingItemRequest,
    ) -> RatingItemResponse:
        """
        创建评分项目。
        """

        # -------------------------
        # 检查名称是否已经存在
        # -------------------------

        exists_stmt = (
            select(RatingItemModel.id)
            .where(
                RatingItemModel.name == request.name
            )
            .limit(1)
        )

        exists_id = self.db.scalar(
            exists_stmt
        )

        if exists_id is not None:
            raise BusinessException(
                code=10001,
                message="评分项目名称已存在",
                status_code=409,
            )

        # -------------------------
        # 创建 ORM 对象
        # -------------------------

        item = RatingItemModel(
            name=request.name,
            description=request.description,

            # 新增项目固定为初始化状态。
            status=int(
                RatingStatus.INITIALIZED
            ),
        )

        self.db.add(item)

        try:
            # 提交事务。
            self.db.commit()

        except IntegrityError:
            # 数据库约束异常必须 rollback，
            # 否则当前 Session 会保持失败状态。
            self.db.rollback()

            # 即使前面已经检查名称是否重复，
            # 高并发情况下仍可能在检查后被其他事务插入。
            # 因此数据库 UNIQUE 约束仍然是最终保障。
            raise BusinessException(
                code=10001,
                message="评分项目名称已存在",
                status_code=409,
            )

        # 重新读取数据库生成的字段：
        # id、create_time、update_time 等。
        self.db.refresh(item)

        return RatingItemResponse.model_validate(
            item
        )

    def update_item(
            self,
            request: UpdateRatingItemRequest,
    ) -> RatingItemResponse:
        """
        修改评分项目。
        """

        # -------------------------
        # 查询待修改的评分项目
        # -------------------------

        stmt = (
            select(RatingItemModel)
            .where(
                RatingItemModel.id == request.id
            )
        )

        item = self.db.scalar(stmt)

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        # -------------------------
        # 检查名称是否被其他记录占用
        # -------------------------

        duplicate_stmt = (
            select(RatingItemModel.id)
            .where(
                RatingItemModel.name == request.name,

                # 排除当前正在修改的记录。
                RatingItemModel.id != request.id,
            )
            .limit(1)
        )

        duplicate_id = self.db.scalar(
            duplicate_stmt
        )

        if duplicate_id is not None:
            raise BusinessException(
                code=10001,
                message="评分项目名称已存在",
                status_code=409,
            )

        # -------------------------
        # 更新允许编辑的字段
        # -------------------------

        item.name = request.name
        item.description = request.description

        # status 属于系统状态，
        # 普通修改接口不允许直接修改。
        try:
            self.db.commit()

        except IntegrityError:
            # 数据库操作失败后必须回滚，
            # 否则 Session 会保持失败状态。
            self.db.rollback()

            raise BusinessException(
                code=10001,
                message="评分项目名称已存在",
                status_code=409,
            )

        # 获取数据库中的最新值，
        # 包括自动更新的 update_time。
        self.db.refresh(item)

        return RatingItemResponse.model_validate(
            item
        )
