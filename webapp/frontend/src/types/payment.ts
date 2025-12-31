export interface PaymentProvider {
  id: 'nowpayments' | 'coinbase'
  name: string
  description: string
  supported_currencies: string[]
  fees: string
  logo: string
}

export interface CryptoPaymentRequest {
  provider: 'nowpayments' | 'coinbase'
  plan: 'premium'
  currency?: string
  amount?: number
}

export interface PaymentResponse {
  payment_id: string
  provider: string
  amount: number
  currency: string
  payment_url?: string
  payment_address?: string
  qr_code?: string
  expires_at: string
  status: 'pending' | 'completed' | 'failed' | 'expired'
}

export interface Subscription {
  id: string
  user_id: string
  plan: 'free' | 'premium'
  status: 'active' | 'cancelled' | 'expired'
  current_period_start: string
  current_period_end: string
  payment_method: string
}

export interface UsageStats {
  daily_usage: number
  daily_limit: number
  monthly_usage: number
  total_usage: number
  plan_features: {
    unlimited_lookups: boolean
    avs_generation: boolean
    bulk_export: boolean
    priority_support: boolean
  }
}

export interface PaymentState {
  providers: PaymentProvider[]
  currentPayment: PaymentResponse | null
  subscription: Subscription | null
  usageStats: UsageStats | null
  isLoading: boolean
  error: string | null
}
