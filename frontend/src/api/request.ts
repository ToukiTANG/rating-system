import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types'

import { ElMessage } from 'element-plus'

/**
 * 创建 Axios 实例
 */
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

/**
 * 请求拦截器
 */
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 如果以后有 token，可以统一在这里添加
    //
    // const token = localStorage.getItem('token')
    //
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }

    return config
  },

  (error: AxiosError) => {
    return Promise.reject(error)
  },
)

/**
 * 响应拦截器
 */
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const result = response.data

    /**
     * 业务成功
     */
    if (result.code === 0) {
      return response
    }

    /**
     * 业务异常
     */
    ElMessage.error(result.message || '请求失败')

    return Promise.reject(new Error(result.message || '请求失败'))
  },

  (error: AxiosError<ApiResponse>) => {
    handleHttpError(error)

    return Promise.reject(error)
  },
)

/**
 * 统一处理 HTTP / 网络异常
 */
function handleHttpError(error: AxiosError<ApiResponse>) {
  /**
   * 请求已经发出，并且后端返回 HTTP 响应
   */
  if (error.response) {
    const status = error.response.status

    const backendMessage = error.response.data?.message

    switch (status) {
      case 400:
        ElMessage.error(backendMessage || '请求参数错误')
        break

      case 401:
        ElMessage.error(backendMessage || '登录状态已失效')

        // 如果有登录系统，可以在这里：
        //
        // localStorage.removeItem('token')
        // router.push('/login')

        break

      case 403:
        ElMessage.error(backendMessage || '没有访问权限')
        break

      case 404:
        ElMessage.error(backendMessage || '请求的资源不存在')
        break

      case 405:
        ElMessage.error(backendMessage || '请求方法不允许')
        break

      case 409:
        ElMessage.error(backendMessage || '数据冲突')
        break

      case 422:
        ElMessage.error(backendMessage || '请求参数校验失败')
        break

      case 500:
        ElMessage.error(backendMessage || '服务器内部错误')
        break

      case 502:
        ElMessage.error('网关错误')
        break

      case 503:
        ElMessage.error('服务暂时不可用')
        break

      case 504:
        ElMessage.error('网关请求超时')
        break

      default:
        ElMessage.error(backendMessage || `请求失败 (${status})`)
    }

    return
  }

  /**
   * 请求发送了，但没有收到响应
   */
  if (error.request) {
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
      return
    }

    if (error.code === 'ERR_NETWORK') {
      ElMessage.error('网络异常，请检查网络或服务器状态')
      return
    }

    ElMessage.error('无法连接服务器')

    return
  }

  /**
   * Axios 自身配置等异常
   */
  ElMessage.error(error.message || '请求发生异常')
}

export async function get<T>(url: string, params?: object): Promise<T> {
  const response = await request.get<ApiResponse<T>>(url, {
    params,
  })

  return response.data.data as T
}

export async function post<T>(url: string, data?: unknown): Promise<T> {
  const response = await request.post<ApiResponse<T>>(url, data)

  return response.data.data as T
}

export default request
