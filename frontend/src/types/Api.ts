export interface ApiResponse<T = unknown> {
  code: number

  data: T | null

  message: string | null
}

export interface PageResult<T> {
  list: T[]
  total: number
}
