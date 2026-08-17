export type RatingStatus = 0 | 1 | 2

export interface SearchForm {
  name: string
  status: null | RatingStatus
}

export interface RatingItem {
  id: number
  name: string
  description: string
  status: RatingStatus
  distinguishExpert: boolean
  expertWeight: number | null
  expertToken: string | null
  createTime: string
  updateTime: string
}

export interface RatingItemQuery {
  name?: string
  status?: RatingStatus
  page: number
  pageSize: number
}

/**
 * 修改评分项目请求参数
 */
export interface UpdateRatingItemRequest {
  id: number
  name: string
  description: string
  distinguishExpert: boolean
  expertWeight: number | null
}

export interface PageResult<T> {
  list: T[]
  total: number
}

export interface RatingStatistics {
  averageScore: number | null
  updateTime: string | null
}
