<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/75 backdrop-blur-sm" @click="closeModal"></div>
        
        <!-- Modal -->
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="relative bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 w-full max-w-lg scale-in">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-700">
              <div>
                <h3 class="text-xl font-bold text-white">Upgrade to Premium</h3>
                <p class="text-gray-400 text-sm mt-1">Choose your payment method</p>
              </div>
              <button @click="closeModal" class="p-2 rounded-lg hover:bg-gray-700 transition-colors">
                <XMarkIcon class="w-5 h-5 text-gray-400" />
              </button>
            </div>
            
            <!-- Content -->
            <div class="p-6 space-y-6">
              <!-- Plan info -->
              <div class="bg-gradient-to-r from-primary-600/10 to-secondary-600/10 rounded-xl p-4 border border-primary-600/20">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-lg font-semibold text-white">Premium Plan</span>
                  <span class="text-2xl font-bold text-white">$9.99</span>
                </div>
                <p class="text-sm text-gray-300">Unlock unlimited card generation and advanced features</p>
              </div>
              
              <!-- Payment providers -->
              <div class="space-y-4">
                <h4 class="font-medium text-white">Select Payment Provider</h4>
                
                <div class="grid gap-3">
                  <button
                    v-for="provider in providers"
                    :key="provider.id"
                    @click="selectedProvider = provider.id"
                    :class="[
                      'relative p-4 rounded-xl border-2 text-left transition-all duration-200 hover:scale-105',
                      selectedProvider === provider.id
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-gray-600 hover:border-gray-500'
                    ]"
                  >
                    <div class="flex items-center justify-between">
                      <div>
                        <div class="font-medium text-white">{{ provider.name }}</div>
                        <div class="text-sm text-gray-400">{{ provider.description }}</div>
                        <div class="text-xs text-gray-500 mt-1">Fee: {{ provider.fees }}</div>
                      </div>
                      <div class="flex items-center space-x-2">
                        <div class="text-xs text-gray-400">
                          {{ provider.supported_currencies.slice(0, 3).join(', ') }}
                          <span v-if="provider.supported_currencies.length > 3">+</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Selection indicator -->
                    <div v-if="selectedProvider === provider.id" 
                         class="absolute top-2 right-2 w-3 h-3 bg-primary-500 rounded-full"></div>
                  </button>
                </div>
              </div>
              
              <!-- Crypto currency selection -->
              <div v-if="selectedProvider" class="space-y-3">
                <h5 class="font-medium text-white text-sm">Choose Cryptocurrency</h5>
                <div class="grid grid-cols-2 gap-2">
                  <button
                    v-for="currency in availableCurrencies"
                    :key="currency"
                    @click="selectedCurrency = currency"
                    :class="[
                      'p-2 rounded-lg border text-sm transition-colors',
                      selectedCurrency === currency
                        ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                        : 'border-gray-600 text-gray-300 hover:border-gray-500'
                    ]"
                  >
                    {{ currency }}
                  </button>
                </div>
              </div>
              
              <!-- Real-time price -->
              <div v-if="cryptoPrice" class="bg-gray-900 rounded-lg p-3 border border-gray-700">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-400">Total Amount:</span>
                  <span class="font-mono text-white">{{ cryptoPrice.amount }} {{ cryptoPrice.currency }}</span>
                </div>
                <div class="text-xs text-gray-500 mt-1">
                  ≈ ${{ cryptoPrice.usd_equivalent }} USD
                </div>
              </div>
              
              <!-- Error message -->
              <div v-if="error" class="bg-red-900/20 border border-red-700 rounded-lg p-3">
                <p class="text-red-400 text-sm">{{ error }}</p>
              </div>
            </div>
            
            <!-- Footer -->
            <div class="flex items-center justify-end space-x-3 p-6 border-t border-gray-700">
              <button @click="closeModal" class="btn btn-ghost">
                Cancel
              </button>
              <button
                @click="createPayment"
                :disabled="!selectedProvider || !selectedCurrency || isLoading"
                class="btn btn-primary"
              >
                <div v-if="isLoading" class="flex items-center">
                  <div class="spinner mr-2"></div>
                  Creating Payment...
                </div>
                <span v-else>Pay with {{ selectedCurrency }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePaymentStore } from '@/stores/payment'
// import type { PaymentProvider } from '@/types'
import { XMarkIcon } from '@heroicons/vue/24/outline'

interface Props {
  show: boolean
  tier: 'premium'
}

interface Emits {
  (e: 'close'): void
  (e: 'payment-created', payment: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Store
const paymentStore = usePaymentStore()

// Local state
const selectedProvider = ref<'nowpayments' | 'coinbase' | null>(null)
const selectedCurrency = ref<string | null>(null)
const cryptoPrice = ref<any>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)

// Computed
const providers = computed(() => paymentStore.providers)

const availableCurrencies = computed(() => {
  if (!selectedProvider.value) return []
  const provider = providers.value.find(p => p.id === selectedProvider.value)
  return provider?.supported_currencies || []
})

// Watchers
watch([selectedProvider, selectedCurrency], async () => {
  if (selectedProvider.value && selectedCurrency.value) {
    await fetchCryptoPrice()
  }
})

// Methods
const closeModal = () => {
  emit('close')
  resetForm()
}

const resetForm = () => {
  selectedProvider.value = null
  selectedCurrency.value = null
  cryptoPrice.value = null
  error.value = null
}

const fetchCryptoPrice = async () => {
  if (!selectedProvider.value || !selectedCurrency.value) return
  
  try {
    // Mock crypto price calculation
    const mockPrices = {
      BTC: { amount: 0.00025, usd_equivalent: 9.99 },
      ETH: { amount: 0.003, usd_equivalent: 9.99 },
      LTC: { amount: 0.15, usd_equivalent: 9.99 },
      USDT: { amount: 9.99, usd_equivalent: 9.99 },
      USDC: { amount: 9.99, usd_equivalent: 9.99 },
    }
    
    cryptoPrice.value = {
      currency: selectedCurrency.value,
      ...mockPrices[selectedCurrency.value as keyof typeof mockPrices]
    }
  } catch (err) {
    console.error('Failed to fetch crypto price:', err)
  }
}

const createPayment = async () => {
  if (!selectedProvider.value || !selectedCurrency.value) return
  
  isLoading.value = true
  error.value = null
  
  try {
    const payment = await paymentStore.createCryptoPayment({
      provider: selectedProvider.value,
      plan: props.tier,
      currency: selectedCurrency.value,
      amount: cryptoPrice.value?.amount,
    })
    
    emit('payment-created', payment)
    closeModal()
    
    // Start polling for payment status
    const paymentData = payment as { payment_id: string }
    paymentStore.startPaymentStatusPolling(paymentData.payment_id)
    
    window.addToast?.({
      type: 'success',
      title: 'Payment created!',
      message: `Pay ${cryptoPrice.value.amount} ${selectedCurrency.value} to complete your upgrade.`,
    })
  } catch (err: any) {
    error.value = err.message || 'Failed to create payment'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-active .scale-in,
.modal-leave-active .scale-in {
  transition: transform 0.3s ease;
}

.modal-enter-from .scale-in,
.modal-leave-to .scale-in {
  transform: scale(0.95);
}
</style>
