export * from './auth'
export * from './bin'
export * from './card'
export * from './payment'

export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: 'success' | 'error'
}

export interface ApiError {
  message: string
  code?: string
  status?: number
  details?: any
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface Theme {
  mode: 'light' | 'dark'
  primary: string
  secondary: string
  accent: string
}

export interface AppSettings {
  theme: Theme
  notifications: {
    email: boolean
    browser: boolean
    payment_updates: boolean
  }
  privacy: {
    analytics: boolean
    marketing: boolean
  }
}
