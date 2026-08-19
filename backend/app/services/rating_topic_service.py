from datetime import datetime
from hmac import compare_digest
from secrets import token_urlsafe

from sqlalchemy import (
    func,
    literal,
    select,
)
from sqlalchemy.dialects.sqlite import (
    insert as sqlite_insert,
)
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.rating_item import RatingItemModel
from app.models.rating_item_participant import (
    RatingItemParticipantModel,
)
from app.models.rating_result import ReviewerType
from app.models.rating_topic import RatingTopicModel
from app.schemas.common import PageResult
from app.schemas.rating import (
    CreateRatingTopicRequest,
    RatingStatus,
    RatingTopicEntryResponse,
    RatingTopicResponse,
    TopicActiveRatingItemResponse,
    UpdateRatingTopicRequest,
)


class RatingTopicService:
    """
    评分主题服务。
    """

    def __init__(
            self,
            db: Session,
    ) -> None:
        self.db = db

    # =========================================================
    # Topic 查询
    # =========================================================

    def list_topics(
            self,
            *,
            name: str | None,
            page: int,
            page_size: int,
    ) -> PageResult[RatingTopicResponse]:
        """
        分页查询评分主题。
        """

        conditions = []

        # -------------------------
        # 名称模糊查询
        # -------------------------

        if name:
            keyword = name.strip()

            if keyword:
                conditions.append(
                    RatingTopicModel.name.ilike(
                        f"%{keyword}%"
                    )
                )

        # -------------------------
        # 查询总数量
        # -------------------------

        count_stmt = (
            select(
                func.count(
                    RatingTopicModel.id
                )
            )
            .where(
                *conditions
            )
        )

        total = (
                self.db.scalar(
                    count_stmt
                )
                or 0
        )

        # -------------------------
        # 分页查询
        # -------------------------

        stmt = (
            select(
                RatingTopicModel
            )
            .where(
                *conditions
            )
            .order_by(
                RatingTopicModel.id.desc()
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(
                page_size
            )
        )

        topics = (
            self.db.scalars(
                stmt
            )
            .all()
        )

        records = [
            RatingTopicResponse.model_validate(
                topic
            )
            for topic in topics
        ]

        return PageResult(
            list=records,
            total=total,
            page=page,
            pageSize=page_size,
        )

    # =========================================================
    # Topic 详情
    # =========================================================

    def get_topic(
            self,
            topic_id: int,
    ) -> RatingTopicResponse:
        """
        获取评分主题详情。
        """

        topic = self.db.get(
            RatingTopicModel,
            topic_id,
        )

        if topic is None:
            raise BusinessException(
                code=11001,
                message="评分主题不存在",
                status_code=404,
            )

        return RatingTopicResponse.model_validate(
            topic
        )

    # =========================================================
    # 创建 Topic
    # =========================================================

    def create_topic(
            self,
            request: CreateRatingTopicRequest,
    ) -> RatingTopicResponse:
        """
        创建评分主题。

        Topic 创建时确定：
        - 是否区分专家
        - 专家评分权重
        - 大众评委人数
        - 专家评委人数
        - 专家 Token

        人数配置创建后不再允许修改。
        """

        # -------------------------
        # 检查名称是否重复
        # -------------------------

        duplicate_stmt = (
            select(
                RatingTopicModel.id
            )
            .where(
                RatingTopicModel.name
                == request.name
            )
            .limit(1)
        )

        duplicate_id = self.db.scalar(
            duplicate_stmt
        )

        if duplicate_id is not None:
            raise BusinessException(
                code=11002,
                message="评分主题名称已存在",
                status_code=409,
            )

        # -------------------------
        # 创建专家 Token
        # -------------------------

        expert_token = (
            token_urlsafe(24)
            if request.distinguish_expert
            else None
        )

        # -------------------------
        # 创建 Topic
        # -------------------------

        topic = RatingTopicModel(
            name=request.name,
            description=request.description,

            distinguish_expert=(
                request.distinguish_expert
            ),

            expert_weight=(
                request.expert_weight
            ),

            public_limit=(
                request.public_limit
            ),

            expert_limit=(
                request.expert_limit
            ),

            expert_token=expert_token,
        )

        self.db.add(
            topic
        )

        self.db.commit()

        self.db.refresh(
            topic
        )

        return RatingTopicResponse.model_validate(
            topic
        )

    # =========================================================
    # 修改 Topic
    # =========================================================

    def update_topic(
            self,
            request: UpdateRatingTopicRequest,
    ) -> RatingTopicResponse:
        """
        修改评分主题。

        创建后固定：
        - distinguish_expert
        - public_limit
        - expert_limit
        - expert_token

        允许修改：
        - name
        - description
        - expert_weight
        """

        # -------------------------
        # 查询 Topic
        # -------------------------

        topic = self.db.get(
            RatingTopicModel,
            request.id,
        )

        if topic is None:
            raise BusinessException(
                code=11001,
                message="评分主题不存在",
                status_code=404,
            )

        # -------------------------
        # 检查名称是否重复
        # -------------------------

        duplicate_stmt = (
            select(
                RatingTopicModel.id
            )
            .where(
                RatingTopicModel.name
                == request.name,

                RatingTopicModel.id
                != request.id,
            )
            .limit(1)
        )

        duplicate_id = self.db.scalar(
            duplicate_stmt
        )

        if duplicate_id is not None:
            raise BusinessException(
                code=11002,
                message="评分主题名称已存在",
                status_code=409,
            )

        # -------------------------
        # 更新专家权重
        # -------------------------

        if topic.distinguish_expert:

            if request.expert_weight is None:
                raise BusinessException(
                    code=11014,
                    message="专家评分主题必须设置专家评分占比",
                    status_code=422,
                )

            topic.expert_weight = (
                request.expert_weight
            )

        else:
            # 未开启专家评分的 Topic
            # 不允许传入专家权重。
            if request.expert_weight is not None:
                raise BusinessException(
                    code=11015,
                    message="当前评分主题未开启专家评分",
                    status_code=422,
                )

        # -------------------------
        # 更新基础信息
        # -------------------------

        topic.name = request.name

        topic.description = (
            request.description
        )

        self.db.commit()

        self.db.refresh(
            topic
        )

        return RatingTopicResponse.model_validate(
            topic
        )

    # =========================================================
    # 删除 Topic
    # =========================================================

    def delete_topic(
            self,
            topic_id: int,
    ) -> None:
        """
        删除评分主题。

        Topic 下存在 RatingItem 时，
        不允许直接删除。
        """

        topic = self.db.get(
            RatingTopicModel,
            topic_id,
        )

        if topic is None:
            raise BusinessException(
                code=11001,
                message="评分主题不存在",
                status_code=404,
            )

        # -------------------------
        # 检查是否存在 RatingItem
        # -------------------------

        item_stmt = (
            select(
                RatingItemModel.id
            )
            .where(
                RatingItemModel.topic_id
                == topic.id
            )
            .limit(1)
        )

        item_id = self.db.scalar(
            item_stmt
        )

        if item_id is not None:
            raise BusinessException(
                code=11003,
                message="当前评分主题下存在评分项目，不能删除",
                status_code=409,
            )

        self.db.delete(
            topic
        )

        self.db.commit()

    # =========================================================
    # 获取 Topic 当前评分入口
    # =========================================================

    def get_rating_entry(
            self,
            *,
            topic_id: int,
            client_id: str,
            expert_token: str | None,
    ) -> RatingTopicEntryResponse:
        """
        获取 Topic 当前评分入口。

        流程：

        1. 查询 Topic
        2. 判断当前客户端的评委身份
        3. 查询当前 status=1 的 RatingItem
        4. 如果没有 active Item，则直接返回
        5. 如果存在 active Item，则申请该 Item 的评分名额
        6. 返回当前 RatingItem

        注意：

        participant 属于 RatingItem，
        而不是 RatingTopic。

        当 distinguish_expert=False 时：
        - 所有参与者仍按 PUBLIC 身份记录
        - 使用 public_limit 控制参与人数
        - 后续评分方式为 0~100 分制

        当 distinguish_expert=True 时：
        - PUBLIC 使用点赞评分
        - EXPERT 使用 0~100 分制
        """

        # -------------------------
        # 查询 Topic
        # -------------------------

        topic = self.db.get(
            RatingTopicModel,
            topic_id,
        )

        if topic is None:
            raise BusinessException(
                code=11001,
                message="评分主题不存在",
                status_code=404,
            )

        # -------------------------
        # 判断评委类型
        # -------------------------
        #
        # 默认按照 PUBLIC 身份进入。
        #
        # 注意：
        #
        # distinguish_expert=False 时，
        # PUBLIC 只是参与者身份，
        # 不代表使用点赞评分。
        #
        # 实际评分方式后续根据
        # topic.distinguish_expert 决定。
        # -------------------------

        reviewer_type = (
            ReviewerType.PUBLIC
        )

        # expertToken 不为空，
        # 表示当前请求希望以专家身份进入。
        if expert_token is not None:

            # Topic 未区分专家 / 大众时，
            # 不存在专家专用入口。
            if not topic.distinguish_expert:
                raise BusinessException(
                    code=11004,
                    message="当前评分主题未开启专家评分",
                    status_code=403,
                )

            # 校验专家 Token。
            if (
                    topic.expert_token is None
                    or not compare_digest(
                expert_token,
                topic.expert_token,
            )
            ):
                raise BusinessException(
                    code=11005,
                    message="专家评分凭证无效",
                    status_code=403,
                )

            reviewer_type = (
                ReviewerType.EXPERT
            )

        # -------------------------
        # 查询当前正在评分的 Item
        # -------------------------

        active_item_stmt = (
            select(
                RatingItemModel
            )
            .where(
                RatingItemModel.topic_id
                == topic.id,

                RatingItemModel.status
                == int(
                    RatingStatus.RATING
                ),
            )
            .limit(1)
        )

        active_item = self.db.scalar(
            active_item_stmt
        )

        # -------------------------
        # 当前没有正在评分的 Item
        # -------------------------
        #
        # 这是正常业务状态。
        #
        # 此时不能占用任何 participant 名额。
        # -------------------------

        if active_item is None:
            return RatingTopicEntryResponse(
                topicId=topic.id,

                topicName=topic.name,

                # 告诉前端当前 Topic
                # 是否区分专家 / 大众。
                distinguishExpert=(
                    topic.distinguish_expert
                ),

                reviewerType=int(
                    reviewer_type
                ),

                activeItem=None,
            )

        # -------------------------
        # 为当前 Item 申请评分资格
        # -------------------------

        self.acquire_participation(
            topic=topic,
            item=active_item,
            client_id=client_id,
            reviewer_type=reviewer_type,
        )

        # -------------------------
        # 返回当前评分项目
        # -------------------------

        return RatingTopicEntryResponse(
            topicId=topic.id,

            topicName=topic.name,

            # 告诉前端当前 Topic
            # 是否区分专家 / 大众。
            distinguishExpert=(
                topic.distinguish_expert
            ),

            reviewerType=int(
                reviewer_type
            ),

            activeItem=(
                TopicActiveRatingItemResponse
                .model_validate(
                    active_item
                )
            ),
        )

    # =========================================================
    # 申请 RatingItem 评分资格
    # =========================================================

    def acquire_participation(
            self,
            *,
            topic: RatingTopicModel,
            item: RatingItemModel,
            client_id: str,
            reviewer_type: ReviewerType,
    ) -> None:
        """
        为当前客户端申请指定 RatingItem 的评分资格。

        Topic 中：

            public_limit
            expert_limit

        表示的是 Topic 下每一个 RatingItem
        分别允许多少大众 / 专家评委。

        例如：

            Topic:
                publicLimit = 100
                expertLimit = 5

            Item A:
                Public <= 100
                Expert <= 5

            Item B:
                Public <= 100
                Expert <= 5

        Item A 和 Item B 的人数互相独立。
        """

        # -------------------------
        # 查询当前客户端是否已经参与该 Item
        # -------------------------

        existing_stmt = (
            select(
                RatingItemParticipantModel
            )
            .where(
                RatingItemParticipantModel.rating_item_id
                == item.id,

                RatingItemParticipantModel.client_id
                == client_id,
            )
            .limit(1)
        )

        existing = self.db.scalar(
            existing_stmt
        )

        # -------------------------
        # 已经取得过资格
        # -------------------------

        if existing is not None:

            # 同一个身份重复进入，
            # 例如刷新页面、重新扫码，
            # 不重复占用名额。
            if (
                    existing.reviewer_type
                    == int(reviewer_type)
            ):
                return

            # 同一个 Item 中，
            # 一个 clientId 只能拥有一种评委身份。
            raise BusinessException(
                code=11009,
                message="当前客户端已以其他评委身份参与该评分项目",
                status_code=409,
            )

        # -------------------------
        # 获取人数上限
        # -------------------------

        if (
                reviewer_type
                == ReviewerType.EXPERT
        ):

            if topic.expert_limit is None:
                raise BusinessException(
                    code=11010,
                    message="评分主题专家人数配置异常",
                    status_code=500,
                )

            limit = (
                topic.expert_limit
            )

        else:
            limit = (
                topic.public_limit
            )

        # -------------------------
        # 当前 Item 已使用人数
        # -------------------------

        used_count = (
            select(
                func.count(
                    RatingItemParticipantModel.id
                )
            )
            .where(
                RatingItemParticipantModel.rating_item_id
                == item.id,

                RatingItemParticipantModel.reviewer_type
                == int(reviewer_type),
            )
            .scalar_subquery()
        )

        # -------------------------
        # 原子申请名额
        # -------------------------
        #
        # INSERT ... SELECT
        #
        # 只有：
        #
        #     used_count < limit
        #
        # 时 SELECT 才会返回一行，
        # INSERT 才会真正执行。
        #
        # SQLite 同一时间写事务会串行，
        # 因此比：
        #
        #     SELECT COUNT
        #     if count < limit
        #     INSERT
        #
        # 分成多个独立操作更加安全。
        # -------------------------

        values_stmt = (
            select(
                literal(
                    item.id
                ),

                literal(
                    client_id
                ),

                literal(
                    int(
                        reviewer_type
                    )
                ),

                literal(
                    datetime.now()
                ),
            )
            .where(
                used_count < limit
            )
        )

        insert_stmt = (
            sqlite_insert(
                RatingItemParticipantModel
            )
            .from_select(
                [
                    "rating_item_id",
                    "client_id",
                    "reviewer_type",
                    "create_time",
                ],
                values_stmt,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "rating_item_id",
                    "client_id",
                ]
            )
        )

        self.db.execute(
            insert_stmt
        )

        # -------------------------
        # 查询最终参与资格
        # -------------------------

        participant = self.db.scalar(
            existing_stmt
        )

        # -------------------------
        # 插入失败
        # -------------------------
        #
        # 最常见原因：
        # 当前评委类型名额已经达到上限。
        # -------------------------

        if participant is None:

            self.db.rollback()

            if (
                    reviewer_type
                    == ReviewerType.EXPERT
            ):
                raise BusinessException(
                    code=11008,
                    message="当前评分项目专家评分名额已满",
                    status_code=409,
                )

            raise BusinessException(
                code=11007,
                message="当前评分项目大众评分名额已满",
                status_code=409,
            )

        # -------------------------
        # 身份冲突保护
        # -------------------------

        if (
                participant.reviewer_type
                != int(reviewer_type)
        ):
            self.db.rollback()

            raise BusinessException(
                code=11009,
                message="当前客户端已以其他评委身份参与该评分项目",
                status_code=409,
            )

        # participant 是独立的资格记录，
        # 在进入评分页面时即正式占用名额。
        self.db.commit()
