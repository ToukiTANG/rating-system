// src/utils/client.ts

const CLIENT_ID_KEY = 'rating_client_id'


/**
 * 获取当前浏览器客户端唯一标识。
 *
 * 第一次进入系统时自动创建，
 * 后续一直保存在 localStorage 中。
 */
export function getClientId(): string {
  let clientId =
    localStorage.getItem(CLIENT_ID_KEY)

  if (!clientId) {
    clientId = crypto.randomUUID()

    localStorage.setItem(
      CLIENT_ID_KEY,
      clientId,
    )
  }

  return clientId
}
