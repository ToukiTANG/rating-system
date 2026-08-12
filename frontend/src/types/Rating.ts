export interface RatingItem {
  id: number
  name: string
  description: string
  // 0初始化，1评分中，2已评分
  status: 0 | 1 | 2
}
