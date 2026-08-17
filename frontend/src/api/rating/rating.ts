import {get, post} from '../request'
import type {
  PageResult,
  RatingItem,
  RatingItemQuery,
  RatingStatistics,
  UpdateRatingItemRequest
} from '@/types'

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
  return post<void>(`/rating/deleteItem`, { id: id })
}

/**
 * 获取单个评分项目。
 */
export function getRatingItem(params: {
  id: number
}) {
  return get<RatingItem>(
    '/rating/getItem',
    params,
  )
}


/**
 * 开始评分。
 */
export function startRating(data: {
  id: number
}) {
  return post<RatingItem>(
    '/rating/startRating',
    data,
  )
}


/**
 * 结束评分。
 */
export function finishRating(data: {
  id: number
}) {
  return post<RatingItem>(
    '/rating/finishRating',
    data,
  )
}

/**
 * 获取实时评分统计。
 */
export function getRatingStatistics(params: {
  id: number
}) {
  return get<RatingStatistics>(
    '/rating/getStatistics',
    params,
  )
}

export interface RatingClientStatus {
  submitted: boolean
  score: number | null
  submitTime: string | null
}

export interface GetRatingStatusParams {
  ratingItemId: number
  clientId: string
}

export interface SubmitScoreRequest {
  ratingItemId: number
  clientId: string
  score: number
  expertToken: string | null
}


/**
 * 查询当前浏览器客户端是否已经评分。
 */
export function getRatingStatus(
  params: GetRatingStatusParams,
) {
  return get<RatingClientStatus>(
    '/rating/getRatingStatus',
    params,
  )
}


/**
 * 提交评分。
 */
export function submitScore(data: SubmitScoreRequest) {
  return post('/rating/submitScore', data)
}
