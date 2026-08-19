from hmac import compare_digest

from sqlalchemy import func, select, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models import RatingResultModel, RatingTopicModel, RatingItemParticipantModel
from app.models.rating_item import RatingItemModel
from app.models.rating_result import ReviewerType
from app.schemas.common import PageResult
from app.schemas.rating import (
    CreateRatingItemRequest,
    RatingItemResponse,
    RatingStatus,
    UpdateRatingItemRequest,
    DeleteRatingItemRequest,
    RatingStatisticsResponse,
    SubmitScoreRequest,
    RatingResultResponse,
    RatingStatusResponse, RatingResultListItemResponse
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
            topic_id: int | None,
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
        if topic_id is not None:
            conditions.append(
                RatingItemModel.topic_id == topic_id
            )

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

        新评分项目必须归属于一个评分主题。
        """

        # -------------------------
        # 查询所属评分主题
        # -------------------------

        topic = self.db.get(
            RatingTopicModel,
            request.topic_id,
        )

        if topic is None:
            raise BusinessException(
                code=10013,
                message="评分主题不存在",
                status_code=404,
            )

        # -------------------------
        # 检查名称是否已经存在
        # -------------------------

        exists_stmt = (
            select(RatingItemModel.id)
            .where(
                # 同一个评分主题内名称不能重复。
                RatingItemModel.topic_id == topic.id,
                RatingItemModel.name == request.name,
            )
            .limit(1)
        )

        exists_id = self.db.scalar(
            exists_stmt
        )

        if exists_id is not None:
            raise BusinessException(
                code=10001,
                message="当前评分主题下评分项目名称已存在",
                status_code=409,
            )

        # -------------------------
        # 创建 ORM 对象
        # -------------------------

        item = RatingItemModel(
            topic_id=topic.id,
            name=request.name,
            description=request.description,
            image_url=request.image_url,

            # 新增项目固定为初始化状态。
            status=int(
                RatingStatus.INITIALIZED
            ),
        )

        self.db.add(item)

        try:
            self.db.commit()


        except IntegrityError:

            self.db.rollback()

            raise BusinessException(
                code=10001,
                message="当前评分主题下评分项目名称已存在",
                status_code=409,
            )

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
                # 只检查当前评分主题中的同名项目。
                RatingItemModel.topic_id == item.topic_id,
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
                message="当前评分主题下评分项目名称已存在",
                status_code=409,
            )

        # -------------------------
        # 更新允许编辑的字段
        # -------------------------

        if request.image_url is not None:
            item.image_url = request.image_url
        item.name = request.name
        item.description = request.description
        # status 属于系统状态，
        # 普通修改接口不允许直接修改。
        try:
            self.db.commit()


        except IntegrityError:

            self.db.rollback()

            raise BusinessException(
                code=10001,
                message="当前评分主题下评分项目名称已存在",
                status_code=409,
            )

        # 获取数据库中的最新值，
        # 包括自动更新的 update_time。
        self.db.refresh(item)

        return RatingItemResponse.model_validate(
            item
        )

    def delete_item(
            self,
            request: DeleteRatingItemRequest,
    ) -> None:
        """
        删除评分项目。
        """

        # -------------------------
        # 查询待删除的数据
        # -------------------------

        item = self.db.get(
            RatingItemModel,
            request.id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        # -------------------------
        # 删除评分项目
        # -------------------------

        self.db.delete(item)

        try:
            # 提交删除事务。
            self.db.commit()

        except IntegrityError:
            # 数据库操作失败后必须回滚，
            # 否则当前 Session 会保持失败状态。
            self.db.rollback()

            # 后续如果评分项目已经被评分任务等数据引用，
            # 外键约束可能导致删除失败。
            raise BusinessException(
                code=10003,
                message="评分项目已被其他数据引用，无法删除",
                status_code=409,
            )

    def get_item(
            self,
            item_id: int,
    ) -> RatingItemResponse:
        """
        根据 ID 查询单个评分项目。
        """

        item = self.db.get(
            RatingItemModel,
            item_id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        return RatingItemResponse.model_validate(
            item
        )

    def start_rating(
            self,
            item_id: int,
    ) -> RatingItemResponse:
        """
        开始评分。

        状态只能从：
            0（初始化）
        修改为：
            1（评分中）

        同一个评分主题下，
        同一时刻只能有一个评分项目处于评分中。
        """

        # -------------------------
        # 查询评分项目
        # -------------------------

        item = self.db.get(
            RatingItemModel,
            item_id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        # -------------------------
        # 必须已经关联评分主题
        # -------------------------

        if item.topic_id is None:
            raise BusinessException(
                code=10011,
                message="评分项目未关联评分主题",
                status_code=409,
            )

        # -------------------------
        # 检查当前项目状态
        # -------------------------

        if item.status != int(
                RatingStatus.INITIALIZED
        ):
            raise BusinessException(
                code=10004,
                message="当前状态不允许开始评分",
                status_code=409,
            )

        # -------------------------
        # 检查同一主题是否已有
        # 正在评分的项目
        # -------------------------

        active_item_stmt = (
            select(RatingItemModel.id)
            .where(
                RatingItemModel.topic_id
                == item.topic_id,

                RatingItemModel.status
                == int(RatingStatus.RATING),

                # 正常情况下当前 item 还是初始化状态，
                # 这里仍然排除自己，使查询语义更明确。
                RatingItemModel.id
                != item.id,
            )
            .limit(1)
        )

        active_item_id = self.db.scalar(
            active_item_stmt
        )

        if active_item_id is not None:
            raise BusinessException(
                code=10012,
                message="当前评分主题已有正在评分的项目",
                status_code=409,
            )

        # -------------------------
        # 开始评分
        # -------------------------

        item.status = int(
            RatingStatus.RATING
        )

        try:
            self.db.commit()

        except IntegrityError:
            # 即使上面已经提前查询，
            # 两个请求并发开始评分时仍然可能：
            #
            # 请求 A：查询 -> 没有活动项目
            # 请求 B：查询 -> 没有活动项目
            # 请求 A：提交成功
            # 请求 B：提交时触发唯一索引
            #
            # 因此数据库约束仍然作为最终保障。
            self.db.rollback()

            raise BusinessException(
                code=10012,
                message="当前评分主题已有正在评分的项目",
                status_code=409,
            )

        # 获取数据库最新值，
        # 包括 update_time。
        self.db.refresh(item)

        return RatingItemResponse.model_validate(
            item
        )

    def finish_rating(
            self,
            item_id: int,
    ) -> RatingItemResponse:
        """
        结束评分。

        状态只能从：
            1（评分中）
        修改为：
            2（已评分）
        """

        item = self.db.get(
            RatingItemModel,
            item_id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        # 只有评分中状态允许结束评分。
        if item.status != int(
                RatingStatus.RATING
        ):
            raise BusinessException(
                code=10005,
                message="当前状态不允许结束评分",
                status_code=409,
            )

        # 更新评分状态。
        item.status = int(
            RatingStatus.RATED
        )

        self.db.commit()

        # 刷新数据库最新数据。
        self.db.refresh(item)

        return RatingItemResponse.model_validate(
            item
        )

    def submit_score(
            self,
            request: SubmitScoreRequest,
    ) -> RatingResultResponse:
        """
        提交评分。

        同一个浏览器客户端，对同一个评分项目
        只能成功提交一次评分。

        评分前必须已经取得当前 RatingTopic
        对应评委类型的参与资格。

        评分规则：

        1. Topic 不区分专家 / 大众：
           - 所有参与者按 PUBLIC 身份记录
           - 所有人使用 0 ~ 100 分制

        2. Topic 区分专家 / 大众：
           - EXPERT 使用 0 ~ 100 分制
           - PUBLIC 使用点赞制，只能提交 1 或 2
        """

        # -------------------------
        # 查询评分项目
        # -------------------------

        item = self.db.get(
            RatingItemModel,
            request.rating_item_id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        # -------------------------
        # 检查评分项目所属主题
        # -------------------------

        if item.topic_id is None:
            raise BusinessException(
                code=10011,
                message="评分项目未关联评分主题",
                status_code=409,
            )

        topic = self.db.get(
            RatingTopicModel,
            item.topic_id,
        )

        if topic is None:
            raise BusinessException(
                code=10013,
                message="评分主题不存在",
                status_code=404,
            )

        # -------------------------
        # 检查评分状态
        # -------------------------

        if item.status != int(
                RatingStatus.RATING
        ):
            raise BusinessException(
                code=10006,
                message="当前项目不允许评分",
                status_code=409,
            )

        # -------------------------
        # 判断本次请求的评委类型
        # -------------------------
        #
        # 默认身份为 PUBLIC。
        #
        # 注意：
        #
        # PUBLIC 这里只代表参与者身份，
        # 并不必然代表使用点赞评分。
        #
        # 当 Topic 不区分专家时，
        # PUBLIC 同样使用 0 ~ 100 分制。
        # -------------------------

        reviewer_type = ReviewerType.PUBLIC

        # 携带 expertToken，
        # 表示本次请求试图以专家身份评分。
        if request.expert_token is not None:

            # Topic 不区分专家时，
            # 不存在专家专用入口。
            if not topic.distinguish_expert:
                raise BusinessException(
                    code=10008,
                    message="当前评分主题未开启专家评分",
                    status_code=403,
                )

            # 校验专家 Token。
            if (
                    topic.expert_token is None
                    or not compare_digest(
                request.expert_token,
                topic.expert_token,
            )
            ):
                raise BusinessException(
                    code=10009,
                    message="专家评分凭证无效",
                    status_code=403,
                )

            reviewer_type = (
                ReviewerType.EXPERT
            )

        # -------------------------
        # 校验 Topic 评分资格
        # -------------------------

        participant_stmt = (
            select(
                RatingItemParticipantModel
            )
            .where(
                RatingItemParticipantModel.rating_item_id
                == item.id,

                RatingItemParticipantModel.client_id
                == request.client_id,
            )
            .limit(1)
        )

        participant = self.db.scalar(
            participant_stmt
        )

        # 没有经过 Topic 入口取得评分资格。
        if participant is None:
            raise BusinessException(
                code=10014,
                message="当前客户端没有该评分主题的评分资格",
                status_code=403,
            )

        # 已取得资格，
        # 但身份与当前入口不一致。
        if (
                participant.reviewer_type
                != int(reviewer_type)
        ):
            raise BusinessException(
                code=10015,
                message="当前评分身份与已登记评委身份不一致",
                status_code=403,
            )

        # =========================================================
        # 校验评分值
        # =========================================================

        if not topic.distinguish_expert:
            # -----------------------------------------------------
            # 不区分专家 / 大众
            # -----------------------------------------------------
            #
            # 此时虽然 participant 身份仍然是 PUBLIC，
            # 但所有参与者统一使用 0 ~ 100 分制。
            # -----------------------------------------------------

            if (
                    request.score < 0
                    or request.score > 100
            ):
                raise BusinessException(
                    code=10016,
                    message="评分必须在 0 到 100 分之间",
                    status_code=422,
                )

        elif reviewer_type == ReviewerType.EXPERT:
            # -----------------------------------------------------
            # 区分专家 / 大众：
            # 专家使用 0 ~ 100 分制。
            # -----------------------------------------------------

            if (
                    request.score < 0
                    or request.score > 100
            ):
                raise BusinessException(
                    code=10016,
                    message="专家评分必须在 0 到 100 分之间",
                    status_code=422,
                )

        else:
            # -----------------------------------------------------
            # 区分专家 / 大众：
            # 大众使用点赞制。
            #
            # 每人只能提交：
            # 1 个赞
            # 或
            # 2 个赞
            # -----------------------------------------------------

            if request.score not in (
                    1,
                    2,
            ):
                raise BusinessException(
                    code=10017,
                    message="大众评分只能选择 1 个赞或 2 个赞",
                    status_code=422,
                )

        # -------------------------
        # 保存评分结果
        # -------------------------
        #
        # 注意：
        #
        # distinguish_expert=False 时，
        # reviewer_type 仍然保存为 PUBLIC。
        #
        # 此时：
        #
        # reviewer_type = PUBLIC
        # score = 0 ~ 100
        #
        # 后续统计逻辑会根据 Topic
        # 判断这是统一百分制评分，
        # 而不是点赞评分。
        # -------------------------

        result = RatingResultModel(
            rating_item_id=item.id,
            client_id=request.client_id,
            reviewer_type=int(
                reviewer_type
            ),
            score=request.score,
        )

        self.db.add(
            result
        )

        try:
            self.db.commit()

        except IntegrityError:
            self.db.rollback()

            # rating_result 当前已有：
            #
            # UNIQUE(rating_item_id, client_id)
            #
            # 因此同一个客户端对同一个 Item
            # 最多只能成功提交一次。
            raise BusinessException(
                code=10007,
                message="您已经提交过评分",
                status_code=409,
            )

        self.db.refresh(
            result
        )

        return RatingResultResponse.model_validate(
            result
        )

    def get_rating_status(
            self,
            item_id: int,
            client_id: str,
    ) -> RatingStatusResponse:
        """
        查询当前客户端是否已经提交评分。
        """

        item = self.db.get(
            RatingItemModel,
            item_id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        stmt = (
            select(RatingResultModel)
            .where(
                RatingResultModel.rating_item_id
                == item_id,
                RatingResultModel.client_id
                == client_id,
            )
        )

        result = self.db.scalar(stmt)

        if result is None:
            return RatingStatusResponse(
                submitted=False,
            )

        return RatingStatusResponse(
            submitted=True,
            score=result.score,
            submitTime=result.create_time,
        )

    def get_statistics(
            self,
            item_id: int,
    ) -> RatingStatisticsResponse:
        """
        获取评分项目实时统计结果。

        评分规则：

        1. 不区分专家 / 大众：
           - 所有参与者统一使用 0 ~ 100 分制；
           - 最终得分 = 所有评分的平均分。

        2. 区分专家 / 大众：
           - 专家使用 0 ~ 100 分制；
           - 大众每人提交 1 个赞或 2 个赞；

           最终得分 =
               专家平均分 × 专家权重
               +
               大众点赞总数 × 大众权重

           其中：

               大众权重 = 1 - 专家权重

        3. 区分专家时，同时返回：
           - 专家评分人数
           - 专家平均分
           - 专家加权得分
           - 大众评分人数
           - 大众点赞总数
           - 大众加权得分
        """

        # =========================================================
        # 查询评分项目
        # =========================================================

        item = self.db.get(
            RatingItemModel,
            item_id,
        )

        if item is None:
            raise BusinessException(
                code=10002,
                message="评分项目不存在",
                status_code=404,
            )

        # =========================================================
        # 检查评分项目所属主题
        # =========================================================

        if item.topic_id is None:
            raise BusinessException(
                code=10011,
                message="评分项目未关联评分主题",
                status_code=409,
            )

        topic = self.db.get(
            RatingTopicModel,
            item.topic_id,
        )

        if topic is None:
            raise BusinessException(
                code=10013,
                message="评分主题不存在",
                status_code=404,
            )

        # =========================================================
        # 不区分专家 / 大众
        # =========================================================
        #
        # 当前业务规则：
        #
        # - 所有参与者统一使用 0 ~ 100 分制；
        # - participant / result 中 reviewer_type
        #   仍然按照 PUBLIC 保存；
        # - 但业务上不存在“点赞”概念；
        # - 最终得分取所有评分的平均值。
        # =========================================================

        if not topic.distinguish_expert:
            stmt = (
                select(
                    # -------------------------
                    # 所有评委平均分
                    # -------------------------
                    #
                    # 没有评分时 AVG 返回 None。
                    # -------------------------

                    func.avg(
                        RatingResultModel.score
                    ),

                    # -------------------------
                    # 总评分人数
                    # -------------------------

                    func.count(
                        RatingResultModel.id
                    ),

                    # -------------------------
                    # 最后一次评分时间
                    # -------------------------

                    func.max(
                        RatingResultModel.create_time
                    ),
                )
                .where(
                    RatingResultModel.rating_item_id
                    == item_id
                )
            )

            (
                average_score,
                rating_count,
                update_time,
            ) = self.db.execute(
                stmt
            ).one()

            rating_count_value = int(
                rating_count
            )

            # -------------------------
            # 当前没有任何评分
            # -------------------------
            #
            # 数据库存储层 AVG 返回 None。
            #
            # finalScore 接口当前仍然使用 number，
            # 因此没有评分时按 0 返回。
            #
            # 前端已经通过 ratingCount === 0
            # 判断是否显示 "--"。
            # -------------------------

            average_score_value = (
                float(
                    average_score
                )
                if average_score is not None
                else 0.0
            )

            return RatingStatisticsResponse(
                # -------------------------
                # 最终得分
                # -------------------------
                #
                # 不区分专家时，
                # 最终得分就是所有评委平均分。
                # -------------------------

                finalScore=round(
                    average_score_value,
                    2,
                ),

                # -------------------------
                # 总评分人数
                # -------------------------

                ratingCount=(
                    rating_count_value
                ),

                # -------------------------
                # 不区分专家 / 大众
                # -------------------------

                distinguishExpert=False,

                # =================================================
                # 专家 / 大众细分统计
                # =================================================
                #
                # 不区分专家时，
                # 这些字段没有业务含义。
                #
                # 虽然数据库 reviewer_type
                # 实际保存为 PUBLIC，
                # 但不能把这些 0~100 分
                # 当成大众点赞数据。
                # =================================================

                expertCount=0,

                expertAverageScore=None,

                expertWeightedScore=0.0,

                publicCount=0,

                publicLikeCount=0,

                publicWeightedScore=0.0,

                # -------------------------
                # 最后更新时间
                # -------------------------

                updateTime=update_time,
            )

        # =========================================================
        # 区分专家 / 大众
        # =========================================================

        if topic.expert_weight is None:
            raise BusinessException(
                code=10010,
                message="评分主题专家权重配置异常",
                status_code=500,
            )

        stmt = (
            select(
                # =================================================
                # 专家平均分
                # =================================================
                #
                # 不使用 COALESCE。
                #
                # 没有专家评分：
                # None
                #
                # 有专家真实提交 0 分：
                # 0
                #
                # 两者业务含义不同。
                # =================================================

                func.avg(
                    case(
                        (
                            RatingResultModel.reviewer_type
                            == int(
                                ReviewerType.EXPERT
                            ),
                            RatingResultModel.score,
                        ),
                        else_=None,
                    )
                ),

                # =================================================
                # 专家评分人数
                # =================================================

                func.coalesce(
                    func.sum(
                        case(
                            (
                                RatingResultModel.reviewer_type
                                == int(
                                    ReviewerType.EXPERT
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),

                # =================================================
                # 大众点赞总数
                # =================================================
                #
                # 大众 score 只允许：
                #
                # 1
                # 2
                #
                # 因此 SUM(score)
                # 就是点赞总数。
                # =================================================

                func.coalesce(
                    func.sum(
                        case(
                            (
                                RatingResultModel.reviewer_type
                                == int(
                                    ReviewerType.PUBLIC
                                ),
                                RatingResultModel.score,
                            ),
                            else_=0,
                        )
                    ),
                    0.0,
                ),

                # =================================================
                # 大众评分人数
                # =================================================

                func.coalesce(
                    func.sum(
                        case(
                            (
                                RatingResultModel.reviewer_type
                                == int(
                                    ReviewerType.PUBLIC
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),

                # =================================================
                # 总评分人数
                # =================================================

                func.count(
                    RatingResultModel.id
                ),

                # =================================================
                # 最后一次评分时间
                # =================================================

                func.max(
                    RatingResultModel.create_time
                ),
            )
            .where(
                RatingResultModel.rating_item_id
                == item_id
            )
        )

        (
            expert_average,
            expert_count,
            public_like_count,
            public_count,
            rating_count,
            update_time,
        ) = self.db.execute(
            stmt
        ).one()

        # =========================================================
        # 专家统计
        # =========================================================

        expert_count_value = int(
            expert_count
        )

        expert_average_value = (
            float(
                expert_average
            )
            if expert_average is not None
            else None
        )

        # -------------------------
        # 最终计算使用值
        # -------------------------
        #
        # 没有专家评分时：
        # 专家贡献按 0 处理。
        # -------------------------

        expert_score_for_calculation = (
            expert_average_value
            if expert_average_value is not None
            else 0.0
        )

        # =========================================================
        # 大众统计
        # =========================================================

        public_count_value = int(
            public_count
        )

        public_like_count_value = float(
            public_like_count
        )

        rating_count_value = int(
            rating_count
        )

        # =========================================================
        # 计算权重
        # =========================================================

        expert_weight = float(
            topic.expert_weight
        )

        public_weight = (
                1 - expert_weight
        )

        # =========================================================
        # 专家加权得分
        # =========================================================
        #
        # 例如：
        #
        # 专家平均分 = 60
        # 专家权重 = 0.6
        #
        # 60 × 0.6 = 36
        # =========================================================

        expert_weighted_score = (
                expert_score_for_calculation
                * expert_weight
        )

        # =========================================================
        # 大众加权得分
        # =========================================================
        #
        # 例如：
        #
        # 点赞总数 = 1
        # 大众权重 = 0.4
        #
        # 1 × 0.4 = 0.4
        # =========================================================

        public_weighted_score = (
                public_like_count_value
                * public_weight
        )

        # =========================================================
        # 最终得分
        # =========================================================

        final_score = (
                expert_weighted_score
                +
                public_weighted_score
        )

        # =========================================================
        # 返回实时统计
        # =========================================================

        return RatingStatisticsResponse(
            # -------------------------
            # 最终得分
            # -------------------------

            finalScore=round(
                final_score,
                2,
            ),

            # -------------------------
            # 总评分人数
            # -------------------------

            ratingCount=(
                rating_count_value
            ),

            # -------------------------
            # 区分专家 / 大众
            # -------------------------

            distinguishExpert=True,

            # =====================================================
            # 专家统计
            # =====================================================

            expertCount=(
                expert_count_value
            ),

            expertAverageScore=(
                round(
                    expert_average_value,
                    2,
                )
                if expert_average_value
                   is not None
                else None
            ),

            expertWeightedScore=round(
                expert_weighted_score,
                2,
            ),

            # =====================================================
            # 大众统计
            # =====================================================

            publicCount=(
                public_count_value
            ),

            publicLikeCount=int(
                public_like_count_value
            ),

            publicWeightedScore=round(
                public_weighted_score,
                2,
            ),

            # -------------------------
            # 最后更新时间
            # -------------------------

            updateTime=update_time,
        )

    def query_results(
            self,
            page: int,
            page_size: int,
            topic_id: int | None = None,
            item_name: str | None = None,
            reviewer_type: int | None = None,
            score: float | None = None,
    ) -> PageResult[RatingResultListItemResponse]:
        """
        分页查询所有评分结果。

        查询评分结果的同时关联评分项目，
        返回评分项目名称等信息。
        """

        # 查询条件。
        conditions = []

        if topic_id is not None:
            conditions.append(
                RatingItemModel.topic_id
                == topic_id
            )

        if item_name:
            conditions.append(
                RatingItemModel.name.contains(
                    item_name.strip()
                )
            )

        if reviewer_type is not None:
            conditions.append(
                RatingResultModel.reviewer_type
                == reviewer_type
            )

        if score is not None:
            conditions.append(
                RatingResultModel.score
                == score
            )

        # =========================
        # 查询总数
        # =========================

        count_stmt = (
            select(
                func.count(
                    RatingResultModel.id
                )
            )
            .join(
                RatingItemModel,
                RatingItemModel.id
                == RatingResultModel.rating_item_id,
            )
            .where(*conditions)
        )

        total = self.db.scalar(
            count_stmt
        ) or 0

        # =========================
        # 查询当前页
        # =========================

        stmt = (
            select(
                RatingResultModel.id,

                RatingItemModel.topic_id.label(
                    "topic_id"
                ),

                RatingTopicModel.name.label(
                    "topic_name"
                ),

                RatingResultModel.rating_item_id,

                RatingItemModel.name.label(
                    "rating_item_name"
                ),

                RatingResultModel.client_id,

                RatingResultModel.reviewer_type,

                RatingResultModel.score,

                RatingResultModel.create_time,
            )
            .join(
                RatingItemModel,
                RatingItemModel.id
                == RatingResultModel.rating_item_id,
            )
            .outerjoin(
                RatingTopicModel,
                RatingTopicModel.id
                == RatingItemModel.topic_id,
            )
            .where(*conditions)
            .order_by(
                RatingResultModel.create_time.desc()
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(
                page_size
            )
        )

        rows = self.db.execute(
            stmt
        ).all()

        items = [
            RatingResultListItemResponse(
                id=row.id,

                topicId=row.topic_id,

                topicName=row.topic_name,

                ratingItemId=row.rating_item_id,

                ratingItemName=row.rating_item_name,

                clientId=row.client_id,

                reviewerType=row.reviewer_type,

                score=row.score,

                createTime=row.create_time,
            )
            for row in rows
        ]

        return PageResult(
            list=items,
            total=total,
            page=page,
            pageSize=page_size,
        )
