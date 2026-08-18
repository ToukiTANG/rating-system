const ratingServerUrl = import.meta.env.VITE_RATING_SERVER_URL

/**
 * 获取大众评分地址。
 */
export function getPublicRatingUrl(topicId: number): string {
  return `${ratingServerUrl}/score/topic/${topicId}`
}

/**
 * 获取专家评分地址。
 */
export function getExpertRatingUrl(topicId: number, expertToken: string): string {
  const url = new URL(`${ratingServerUrl}/score/topic/${topicId}`)

  url.searchParams.set('expertToken', expertToken)

  return url.toString()
}
