import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as userApi from '@/api/user'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const data = await userApi.login(email, password)
    token.value = data.token
    user.value = data.user
    localStorage.setItem('auth_token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  async function register(name: string, email: string, password: string, passwordConfirmation: string) {
    const data = await userApi.register(name, email, password, passwordConfirmation)
    token.value = data.token
    user.value = data.user
    localStorage.setItem('auth_token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  async function logout() {
    try {
      await userApi.logout()
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
    }
  }

  async function fetchProfile() {
    if (!token.value) return
    try {
      user.value = await userApi.fetchProfile()
      localStorage.setItem('user', JSON.stringify(user.value))
    } catch {
      await logout()
    }
  }

  // Hydrate from localStorage
  const stored = localStorage.getItem('user')
  if (stored) {
    try { user.value = JSON.parse(stored) } catch { /* ignore */ }
  }

  return { user, token, isAuthenticated, login, register, logout, fetchProfile }
})
