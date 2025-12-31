import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import type { User, LoginRequest, RegisterRequest, AuthResponse } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isPremium = computed(() => user.value?.plan === 'premium')
  const isFree = computed(() => user.value?.plan === 'free')

  // Actions
  const login = async (credentials: LoginRequest) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.login(credentials.username, credentials.password)
      const authData: AuthResponse = response.data

      token.value = authData.access_token
      user.value = authData.user

      // Store token in localStorage
      localStorage.setItem('auth_token', authData.access_token)
      localStorage.setItem('user_data', JSON.stringify(authData.user))

      return true
    } catch (err: any) {
      console.error('Login error:', err)
      error.value = err.response?.data?.detail || err.message || 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  const register = async (data: RegisterRequest) => {
    isLoading.value = true
    error.value = null

    try {
      await apiClient.register(data.username, data.email, data.password)
      
      // Auto-login after registration
      return await login({
        username: data.username,
        password: data.password,
      })
    } catch (err: any) {
      console.error('Registration error:', err)
      error.value = err.response?.data?.detail || err.message || 'Registration failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    error.value = null

    // Clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
  }

  const refreshUser = async () => {
    if (!token.value) return

    try {
      const userData = await apiClient.getCurrentUser()
      user.value = userData as User
      localStorage.setItem('user_data', JSON.stringify(userData))
    } catch (err: any) {
      console.error('Failed to refresh user data:', err)
      // If refresh fails, logout user
      logout()
    }
  }

  const initAuth = () => {
    // Restore auth state from localStorage
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('user_data')

    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
        // Refresh user data to ensure it's current
        refreshUser()
      } catch (err) {
        // If user data is corrupted, clear everything
        logout()
      }
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    isPremium,
    isFree,
    
    // Actions
    login,
    register,
    logout,
    refreshUser,
    initAuth,
    clearError,
  }
})
