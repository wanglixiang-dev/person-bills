import { defineStore } from 'pinia'
import type { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  lastCode: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    lastCode: '246810',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
  },
  actions: {
    sendCode() {
      this.lastCode = '246810'
      return this.lastCode
    },
    login(email: string) {
      this.user = { id: 1, email }
      this.token = 'mock-access-token'
    },
    logout() {
      this.user = null
      this.token = null
    },
  },
})
