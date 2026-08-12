import { get, post } from '../request'

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
  createTime: string
  updateTime: string
}

export interface RatingItemQuery {
  name?: string
  status?: RatingStatus
  page: number
  pageSize: number
}

export interface PageResult<T> {
  list: T[]
  total: number
}

/**
 * 获取评分项目列表
 */
export function getRatingItemList(params: RatingItemQuery) {
  return get<PageResult<RatingItem>>('/rating/items', params as unknown as Record<string, unknown>)
}

/**
 * 新增评分项目
 */
export function createRatingItem(data: Partial<RatingItem>) {
  return post<RatingItem>('/rating/addItem', data)
}

/**
 * 修改评分项目
 */
export function updateRatingItem(data: Partial<RatingItem>) {
  return post<RatingItem>(`/rating/updateItem`, data)
}

/**
 * 删除评分项目
 */
export function deleteRatingItem(id: number) {
  return post<void>(`/rating/deleteItems`,id)
}
