export interface RatingTopic {
  id: number

  name: string

  description: string

  /**
   * 是否区分专家评委。
   *
   * Topic 创建后不可修改。
   */
  distinguishExpert: boolean

  /**
   * 专家评分权重。
   *
   * 例如：
   * 0.6 = 专家占 60%
   *
   * 未开启专家评分时为 null。
   */
  expertWeight: number | null

  /**
   * 每个 RatingItem 允许的大众评委人数。
   *
   * Topic 创建后不可修改。
   */
  publicLimit: number

  /**
   * 每个 RatingItem 允许的专家评委人数。
   *
   * 未开启专家评分时为 null。
   * Topic 创建后不可修改。
   */
  expertLimit: number | null

  /**
   * 专家评分凭证。
   *
   * 仅开启专家评分时存在。
   */
  expertToken: string | null

  createTime: string

  updateTime: string
}

export interface RatingTopicQueryParams {
  name?: string
  page?: number
  pageSize?: number
}

export interface RatingTopicCreateRequest {
  name: string

  description: string

  distinguishExpert: boolean

  expertWeight: number | null

  publicLimit: number

  expertLimit: number | null
}

export interface RatingTopicUpdateRequest {
  id: number

  name: string

  description: string

  /**
   * Topic 开启专家评分时必填；
   * 未开启专家评分时传 null。
   */
  expertWeight: number | null
}

export interface RatingTopicDeleteRequest {
  id: number
}

export interface TopicActiveRatingItem {
  id: number

  topicId: number

  name: string

  description: string

  status: 0 | 1 | 2
}

export interface RatingTopicEntry {
  topicId: number

  topicName: string

  /**
   * 0 = 大众评委
   * 1 = 专家评委
   */
  reviewerType: 0 | 1

  /**
   * 当前 Topic 没有正在评分的 Item 时为 null。
   */
  activeItem: TopicActiveRatingItem | null
}
