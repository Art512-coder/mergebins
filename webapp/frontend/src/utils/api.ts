import axios, { type AxiosInstance, type AxiosResponse, type AxiosError } from 'axios'
import type { ApiError } from '@/types'

class ApiClient {
  private readonly instance: AxiosInstance
  private readonly baseURL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'
  
  constructor() {
    this.instance = axios.create({
      baseURL: this.baseURL,
      timeout: 15000, // Increased timeout for D1 queries
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    this.setupInterceptors()
  }
  
  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config: any) => {
        const token = localStorage.getItem('auth_token')
        // Only add auth header for protected endpoints
        if (token && !this.isPublicEndpoint(config.url)) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error: any) => Promise.reject(new Error(error.message || 'Request failed'))
    )
    
    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        const apiError: ApiError = {
          message: 'An unexpected error occurred',
          status: error.response?.status,
        }
        
        if (error.response?.status === 401 && !this.isPublicEndpoint(error.config?.url)) {
          // Token expired or invalid for protected endpoints
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
          apiError.message = 'Session expired. Please login again.'
        } else if (error.response?.status === 403) {
          apiError.message = 'Access denied. Insufficient permissions.'
        } else if (error.response?.status === 429) {
          apiError.message = 'Too many requests. Please try again later.'
        } else if (error.response?.data && typeof error.response.data === 'object' && 'detail' in error.response.data) {
          apiError.message = (error.response.data as { detail: string }).detail
        } else if (error.message === 'Network Error') {
          apiError.message = 'Network error. Please check your connection.'
        }
        
        return Promise.reject(new Error(apiError.message))
      }
    )
  }
  
  private isPublicEndpoint(url?: string): boolean {
    if (!url) return false
    
    const publicEndpoints = [
      '/api/v1/bins/lookup',
      '/api/v1/bins/search',
      '/api/v1/bins/stats',
      '/api/v1/bins/brands',
      '/api/v1/bins/countries',
      '/api/v1/cards/ip-status',
      '/api/v1/cards/avs/countries'
    ]
    
    return publicEndpoints.some(endpoint => url.includes(endpoint))
  }
  
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.instance.get<T>(url, { params })
    return response.data
  }
  
  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.instance.post<T>(url, data)
    return response.data
  }
  
  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.instance.put<T>(url, data)
    return response.data
  }
  
  async delete<T>(url: string): Promise<T> {
    const response = await this.instance.delete<T>(url)
    return response.data
  }
  
  // Specific API methods
  
  // Authentication
  async login(username: string, password: string) {
    return this.instance.post('/api/v1/auth/token', {
      username,
      password,
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }
  
  async register(username: string, email: string, password: string) {
    return this.post('/api/v1/auth/register', {
      username,
      email,
      password,
    })
  }
  
  async getCurrentUser() {
    return this.get('/api/v1/auth/me')
  }
  
  // BIN Lookup
  async lookupBIN(bin: string) {
    return this.get(`/api/v1/bins/lookup/${bin}`)
  }
  
  async getBINHistory() {
    return this.get('/api/v1/bins/history')
  }
  
  // Card Generation
  async generateCards(request: any) {
    return this.post('/api/generate', request)
  }
  
  async getCardGenerationStatus() {
    return this.get('/api/ip-status')
  }

  async exportCards(format: string, cards: any[]) {
    return this.post(`/api/export/${format}`, { cards })
  }  // Payments
  async createCryptoPayment(request: any) {
    return this.post('/api/v1/payments/create-crypto-payment', request)
  }
  
  async getPaymentStatus(paymentId: string) {
    return this.get(`/api/v1/payments/status/${paymentId}`)
  }
  
  async getSubscription() {
    return this.get('/api/v1/payments/subscription')
  }
  
  async getUsageStats() {
    return this.get('/api/v1/auth/usage')
  }
}

export const apiClient = new ApiClient()
