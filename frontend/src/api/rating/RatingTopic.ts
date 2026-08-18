import { get, post } from '@/api/request'


import type {
  PageResult,
  RatingTopic,
  RatingTopicCreateRequest,
  RatingTopicDeleteRequest,
  RatingTopicEntry,
  RatingTopicQueryParams,
  RatingTopicUpdateRequest,
} from '@/types'

/**
 * 分页查询评分主题。
 */
export function queryRatingTopic(params: RatingTopicQueryParams): Promise<PageResult<RatingTopic>> {
  return get<PageResult<RatingTopic>>('/ratingTopic/query', params)
}

/**
 * 查询评分主题详情。
 */
export function getRatingTopic(id: number): Promise<RatingTopic> {
  return get<RatingTopic>('/ratingTopic/get', {
    id,
  })
}

/**
 * 新增评分主题。
 */
export function addRatingTopic(data: RatingTopicCreateRequest): Promise<RatingTopic> {
  return post<RatingTopic>('/ratingTopic/add', data)
}

/**
 * 修改评分主题。
 */
export function updateRatingTopic(data: RatingTopicUpdateRequest): Promise<RatingTopic> {
  return post<RatingTopic>('/ratingTopic/update', data)
}

/**
 * 删除评分主题。
 */
export function deleteRatingTopic(data: RatingTopicDeleteRequest): Promise<boolean> {
  return post<boolean>('/ratingTopic/delete', data)
}

/**
 * 查询 Topic 当前评分入口。
 *
 * 普通入口：
 * 不传 expertToken。
 *
 * 专家入口：
 * 传 Topic 的 expertToken。
 */
export function getRatingTopicEntry(params: { topicId: number; clientId: string; expertToken?: string }): Promise<RatingTopicEntry> {
  return get<RatingTopicEntry>('/ratingTopic/entry', params)
}
