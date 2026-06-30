import { apiRequest, tokenStore } from './client'
import type { User } from '../types'

export interface TokenResponse {
  access_token: string
  expires_in: number
  token_type: string
  user: User
}

export const authApi = {
  sendCode: (email: string, purpose: 'register' | 'login') =>
    apiRequest<{ message: string; dev_code?: string }>('/auth/send-code', {
      method: 'POST',
      body: JSON.stringify({ email, purpose }),
    }),
  register: (email: string, code: string, password?: string) =>
    apiRequest<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, code, password: password || undefined }),
    }),
  loginByCode: (email: string, code: string) =>
    apiRequest<TokenResponse>('/auth/login/code', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),
  loginByPassword: (email: string, password: string) =>
    apiRequest<TokenResponse>('/auth/login/password', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => apiRequest<User>('/auth/me'),
  logout: () => apiRequest<{ message: string }>('/auth/logout', { method: 'POST' }).finally(() => tokenStore.clear()),
}

export function persistToken(response: TokenResponse) {
  tokenStore.set(response.access_token)
  return response
}
