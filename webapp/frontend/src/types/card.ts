export interface GeneratedCard {
  number: string
  cvv: string
  expiry_month: string
  expiry_year: string
  expiry: string
  brand: string
  type: string
  country: string
  bank?: string
  avs_address?: string
  avs_postal?: string
  generated_at: string
}

export interface CardGenerationRequest {
  bin?: string
  count: number
  format: 'json' | 'csv' | 'txt'
  include_avs?: boolean
  custom_expiry?: {
    month: string
    year: string
  }
}

export interface CardGenerationResponse {
  cards: GeneratedCard[]
  total: number
  format: string
  generated_at: string
}

export interface CardGeneratorState {
  cards: GeneratedCard[]
  isLoading: boolean
  error: string | null
  lastGeneration: CardGenerationResponse | null
  exportFormats: string[]
}
