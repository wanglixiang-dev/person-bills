const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export class ApiError extends Error {
  code: string
  status: number

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

export const tokenStore = {
  get: () => sessionStorage.getItem('access_token'),
  set: (token: string) => sessionStorage.setItem('access_token', token),
  clear: () => sessionStorage.removeItem('access_token'),
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json')
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })
  if (!response.ok) {
    let code = 'REQUEST_FAILED'
    let message = '请求失败'
    try {
      const data = await response.json()
      code = data.detail?.code || data.code || code
      message = data.detail?.message || data.message || message
    } catch {
      message = response.statusText
    }
    throw new ApiError(response.status, code, message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
