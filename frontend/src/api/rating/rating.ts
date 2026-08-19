import { get, post } from '../request'

import type {
  AddRatingItemRequest,
  PageResult,
  QueryRatingResultParams,
  RatingItem,
  RatingItemQueryParams,
  RatingResultItem,
  RatingStatistics,
  UpdateRatingItemRequest,
} from '@/types'

/**
 * 获取评分项目列表。
 */
export function getRatingItemList(params: RatingItemQueryParams) {
  return get<PageResult<RatingItem>>('/rating/items', params as unknown as Record<string, unknown>)
}

/**
 * 新增评分项目。
 *
 * 新增时必须指定所属 Topic。
 */
export function createRatingItem(data: AddRatingItemRequest) {
  return post<RatingItem>('/rating/addItem', data)
}

/**
 * 修改评分项目。
 *
 * RatingItem 创建后不允许修改所属 Topic。
 */
export function updateRatingItem(data: UpdateRatingItemRequest) {
  return post<RatingItem>('/rating/updateItem', data)
}

/**
 * 删除评分项目。
 */
export function deleteRatingItem(id: number) {
  return post<void>('/rating/deleteItem', {
    id,
  })
}

/**
 * 获取单个评分项目。
 */
export function getRatingItem(params: { id: number }) {
  return get<RatingItem>('/rating/getItem', params)
}

/**
 * 开始评分。
 */
export function startRating(data: { id: number }) {
  return post<RatingItem>('/rating/startRating', data)
}

/**
 * 结束评分。
 */
export function finishRating(data: { id: number }) {
  return post<RatingItem>('/rating/finishRating', data)
}

/**
 * 获取实时评分统计。
 */
export function getRatingStatistics(params: { id: number }) {
  return get<RatingStatistics>('/rating/getStatistics', params)
}

/**
 * 当前客户端针对某个 RatingItem
 * 的评分提交状态。
 */
export interface RatingClientStatus {
  submitted: boolean

  /**
   * 专家：
   * 0 ~ 100
   *
   * 大众：
   * 1 或 2，表示点赞数量。
   *
   * 未评分：
   * null
   */
  score: number | null

  submitTime: string | null
}

export interface GetRatingStatusParams {
  ratingItemId: number
  clientId: string
}

/**
 * 提交评分请求。
 *
 * score：
 *
 * 专家评委：
 * 0 ~ 100
 *
 * 大众评委：
 * 1 或 2
 */
export interface SubmitScoreRequest {
  ratingItemId: number

  clientId: string

  score: number

  /**
   * 大众评委不传。
   *
   * 专家评委从 Topic 专家二维码
   * URL 中获取。
   */
  expertToken?: string
}

/**
 * 查询当前浏览器客户端是否已经评分。
 */
export function getRatingStatus(params: GetRatingStatusParams) {
  return get<RatingClientStatus>('/rating/getRatingStatus', params)
}

/**
 * 提交评分。
 */
export function submitScore(data: SubmitScoreRequest) {
  return post('/rating/submitScore', data)
}

/**
 * 查询评分结果列表。
 */
export function queryRatingResults(params: QueryRatingResultParams): Promise<PageResult<RatingResultItem>> {
  return get<PageResult<RatingResultItem>>('/rating/queryResults', params)
}

/**
 * RatingItem 图片上传结果。
 */
export interface UploadItemImageResponse {
  url: string
}

/**
 * 上传 RatingItem 图片。
 *
 * 文件上传使用 multipart/form-data，
 * 不能使用普通 JSON post() 封装。
 */
/**
 * 上传 RatingItem 图片。
 */
export interface UploadItemImageResponse {
  url: string
}

/**
 * 上传 RatingItem 图片。
 */
export function uploadItemImage(file: File): Promise<UploadItemImageResponse> {
  const formData = new FormData()

  formData.append('file', file, file.name)

  return post<UploadItemImageResponse>('/rating/uploadItemImage', formData)
}
