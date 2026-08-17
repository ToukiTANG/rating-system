/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string

  /**
   * 对外评分页面服务器地址。
   *
   * 用于生成用户扫码访问的二维码。
   */
  readonly VITE_RATING_SERVER_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
