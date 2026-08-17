/**
 * 对外评分服务器地址。
 */
const ratingServerUrl = import.meta.env.VITE_RATING_SERVER_URL

/**
 * 生成大众评分地址。
 */
export function getPublicRatingUrl(ratingItemId: number): string {
  return new URL(`/score/${ratingItemId}`, ratingServerUrl).toString()
}

/**
 * 生成专家评分地址。
 */
export function getExpertRatingUrl(ratingItemId: number, expertToken: string): string {
  const url = new URL(`/score/${ratingItemId}`, ratingServerUrl)

  url.searchParams.set('expertToken', expertToken)

  return url.toString()
}
