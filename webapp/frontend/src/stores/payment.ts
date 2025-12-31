import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import type { PaymentProvider, PaymentResponse, Subscription, UsageStats, CryptoPaymentRequest } from '@/types'

export const usePaymentStore = defineStore('payment', () => {
  // State
  const providers = ref<PaymentProvider[]>([
    {
      id: 'nowpayments',
      name: 'NOWPayments',
      description: 'Supports 200+ cryptocurrencies',
      supported_currencies: ['BTC', 'ETH', 'LTC', 'USDT', 'USDC'],
      fees: '0.5%',
      logo: '/logos/nowpayments.svg',
    },
    {
      id: 'coinbase',
      name: 'Coinbase Commerce',
      description: 'Secure payments via Coinbase',
      supported_currencies: ['BTC', 'ETH', 'LTC', 'BCH'],
      fees: '1%',
      logo: '/logos/coinbase.svg',
    },
  ])
  
  const currentPayment = ref<PaymentResponse | null>(null)
  const subscription = ref<Subscription | null>(null)
  const usageStats = ref<UsageStats | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isPaymentPending = computed(() => 
    currentPayment.value?.status === 'pending'
  )
  
  const dailyUsagePercentage = computed(() => {
    if (!usageStats.value) return 0
    return (usageStats.value.daily_usage / usageStats.value.daily_limit) * 100
  })
  
  const hasReachedDailyLimit = computed(() => {
    if (!usageStats.value) return false
    return usageStats.value.daily_usage >= usageStats.value.daily_limit
  })

  // Actions
  const createCryptoPayment = async (request: CryptoPaymentRequest) => {
    isLoading.value = true
    error.value = null

    try {
      const payment = await apiClient.createCryptoPayment(request)
      currentPayment.value = payment as PaymentResponse
      return payment
    } catch (err: any) {
      error.value = err.message || 'Failed to create payment'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const checkPaymentStatus = async (paymentId: string) => {
    try {
      const status = await apiClient.getPaymentStatus(paymentId) as { status: string }
      if (currentPayment.value && currentPayment.value.payment_id === paymentId) {
        currentPayment.value.status = status.status as 'pending' | 'completed' | 'failed' | 'expired'
      }
      return status
    } catch (err: any) {
      console.error('Failed to check payment status:', err)
    }
  }

  const loadSubscription = async () => {
    try {
      const sub = await apiClient.getSubscription()
      subscription.value = sub as Subscription
    } catch (err: any) {
      console.error('Failed to load subscription:', err)
    }
  }

  const loadUsageStats = async () => {
    try {
      const stats = await apiClient.getUsageStats()
      usageStats.value = stats as UsageStats
    } catch (err: any) {
      console.error('Failed to load usage stats:', err)
    }
  }

  const clearCurrentPayment = () => {
    currentPayment.value = null
  }

  const clearError = () => {
    error.value = null
  }

  // Auto-refresh payment status
  const startPaymentStatusPolling = (paymentId: string) => {
    const interval = setInterval(async () => {
      const status = await checkPaymentStatus(paymentId) as { status: string } | undefined
      
      if (status && ['completed', 'failed', 'expired'].includes(status.status)) {
        clearInterval(interval)
        
        if (status.status === 'completed') {
          // Refresh user data and usage stats
          await loadSubscription()
          await loadUsageStats()
        }
      }
    }, 10000) // Check every 10 seconds

    // Stop polling after 30 minutes
    setTimeout(() => clearInterval(interval), 30 * 60 * 1000)
  }

  return {
    // State
    providers,
    currentPayment,
    subscription,
    usageStats,
    isLoading,
    error,
    
    // Getters
    isPaymentPending,
    dailyUsagePercentage,
    hasReachedDailyLimit,
    
    // Actions
    createCryptoPayment,
    checkPaymentStatus,
    loadSubscription,
    loadUsageStats,
    clearCurrentPayment,
    clearError,
    startPaymentStatusPolling,
  }
})
