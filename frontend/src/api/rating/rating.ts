import { get, post } from '../request'
import type { RatingItemQuery, PageResult, RatingItem, UpdateRatingItemRequest } from '@/types'

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
export function updateRatingItem(data: UpdateRatingItemRequest) {
  return post<RatingItem>('/rating/updateItem', data)
}

/**
 * 删除评分项目
 */
export function deleteRatingItem(id: number) {
  return post<void>(`/rating/deleteItems`, id)
}
