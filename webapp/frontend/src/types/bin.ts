export interface BINResult {
  bin: string
  scheme?: string
  brand?: string
  type?: string
  level?: string
  country?: string
  country_name?: string
  country_code?: string
  issuer?: string
  bank?: string
  bank_name?: string
  bank_url?: string
  bank_phone?: string
  valid: boolean
}

export interface BINSearchRequest {
  bin: string
  include_bank_info?: boolean
}

export interface BINSearchHistory {
  id: string
  bin: string
  result: BINResult
  searched_at: string
  user_id: string
}

export interface BINSearchState {
  query: string
  result: BINResult | null
  history: BINSearchHistory[]
  isLoading: boolean
  error: string | null
  favorites: string[]
}
