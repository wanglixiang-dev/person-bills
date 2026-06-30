import { defineStore } from 'pinia'
import { authApi, persistToken, type TokenResponse } from '../api/auth'
import { tokenStore } from '../api/client'
import type { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  lastCode: string
  error: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: tokenStore.get(),
    lastCode: '246810',
    error: '',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
  },
  actions: {
    async bootstrap() {
      if (!this.token || this.user) return
      try {
        this.user = await authApi.me()
      } catch {
        this.logoutLocal()
      }
    },
    async sendCode(email: string, purpose: 'register' | 'login') {
      const response = await authApi.sendCode(email, purpose)
      this.lastCode = response.dev_code || ''
      return this.lastCode
    },
    setSession(response: TokenResponse) {
      const saved = persistToken(response)
      this.token = saved.access_token
      this.user = saved.user
      this.error = ''
    },
    async register(email: string, code: string, password?: string) {
      const response = await authApi.register(email, code, password)
      this.setSession(response)
    },
    async loginByCode(email: string, code: string) {
      const response = await authApi.loginByCode(email, code)
      this.setSession(response)
    },
    async loginByPassword(email: string, password: string) {
      const response = await authApi.loginByPassword(email, password)
      this.setSession(response)
    },
    logoutLocal() {
      this.user = null
      this.token = null
      tokenStore.clear()
    },
    async logout() {
      try {
        if (this.token) await authApi.logout()
      } finally {
        this.logoutLocal()
      }
    },
  },
})
