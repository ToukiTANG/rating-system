export type RatingStatus = 0 | 1 | 2

export interface SearchForm {
  topicId: number | null
  name: string
  status: RatingStatus | null
}

export interface RatingItem {
  id: number

  /**
   * 所属评分主题。
   *
   * 当前保留 null，
   * 用于兼容历史 RatingItem 数据。
   */
  topicId: number

  name: string

  description: string

  /**
   * 项目图片 CDN 地址。
   *
   * 历史项目可能没有图片。
   */
  imageUrl: string | null

  status: RatingStatus

  createTime: string

  updateTime: string
}

export interface RatingItemQueryParams {
  topicId?: number
  name?: string
  status?: RatingStatus
  page?: number
  pageSize?: number
}

/**
 * 新增评分项目请求参数。
 */
export interface AddRatingItemRequest {
  topicId: number
  name: string
  description: string
  /**
   * 新增 RatingItem 时图片必填。
   */
  imageUrl: string
}

/**
 * 修改评分项目请求参数。
 *
 * RatingItem 创建后不能修改所属 Topic，
 * 因此这里不包含 topicId。
 */
export interface UpdateRatingItemRequest {
  id: number
  name: string
  description: string
}

/**
 * 实时评分统计。
 */
export interface RatingStatistics {
  finalScore: number

  ratingCount: number

  distinguishExpert: boolean

  expertCount: number

  expertAverageScore: number | null

  expertWeightedScore: number

  publicCount: number

  publicLikeCount: number

  publicWeightedScore: number

  updateTime: string | null
}

/**
 * 评委类型。
 *
 * 0 = 大众评委
 * 1 = 专家评委
 */
export type ReviewerType = 0 | 1

export interface QueryRatingResultParams {
  page: number
  pageSize: number

  topicId?: number

  itemName?: string
  reviewerType?: ReviewerType
  score?: number
}

/**
 * 评分结果列表项。
 */
export interface RatingResultItem {
  id: number

  topicId: number | null

  topicName: string | null

  ratingItemId: number

  ratingItemName: string

  clientId: string

  reviewerType: ReviewerType

  score: number

  createTime: string
}
