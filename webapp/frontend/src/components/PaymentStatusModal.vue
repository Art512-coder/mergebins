<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/80 backdrop-blur-sm"></div>
        
        <!-- Modal -->
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="relative bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 w-full max-w-md">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-700">
              <div>
                <h3 class="text-xl font-bold text-white">Complete Payment</h3>
                <p class="text-gray-400 text-sm mt-1">
                  Send {{ payment?.pay_amount }} {{ payment?.pay_currency }}
                </p>
              </div>
              <button @click="closeModal" class="p-2 rounded-lg hover:bg-gray-700 transition-colors">
                <XMarkIcon class="w-5 h-5 text-gray-400" />
              </button>
            </div>
            
            <!-- Content -->
            <div class="p-6 space-y-6">
              <!-- Payment Status -->
              <div class="text-center">
                <div :class="[
                  'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-4',
                  getStatusColor(payment?.payment_status)
                ]">
                  <div class="w-2 h-2 rounded-full mr-2" :class="getStatusDotColor(payment?.payment_status)"></div>
                  {{ getStatusText(payment?.payment_status) }}
                </div>
              </div>

              <!-- QR Code -->
              <div v-if="payment?.payment_status === 'waiting'" class="text-center">
                <div class="bg-white p-4 rounded-xl inline-block mb-4">
                  <div ref="qrCodeElement" class="w-48 h-48"></div>
                </div>
                
                <!-- Payment Address -->
                <div class="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    Payment Address
                  </label>
                  <div class="flex items-center space-x-2">
                    <input
                      :value="payment?.pay_address"
                      readonly
                      class="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono"
                    />
                    <button
                      @click="copyAddress"
                      class="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                      title="Copy address"
                    >
                      <DocumentDuplicateIcon class="w-4 h-4 text-gray-300" />
                    </button>
                  </div>
                </div>

                <!-- Amount -->
                <div class="bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    Exact Amount
                  </label>
                  <div class="flex items-center space-x-2">
                    <input
                      :value="`${payment?.pay_amount} ${payment?.pay_currency}`"
                      readonly
                      class="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white font-mono"
                    />
                    <button
                      @click="copyAmount"
                      class="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                      title="Copy amount"
                    >
                      <DocumentDuplicateIcon class="w-4 h-4 text-gray-300" />
                    </button>
                  </div>
                </div>

                <!-- Timer -->
                <div v-if="timeRemaining > 0" class="text-center">
                  <p class="text-sm text-gray-400">
                    Payment expires in: 
                    <span class="font-mono text-yellow-400">{{ formatTime(timeRemaining) }}</span>
                  </p>
                </div>

                <!-- Instructions -->
                <div class="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
                  <h4 class="font-medium text-blue-400 mb-2">Payment Instructions</h4>
                  <ol class="text-sm text-gray-300 space-y-1">
                    <li>1. Send exactly <strong>{{ payment?.pay_amount }} {{ payment?.pay_currency }}</strong></li>
                    <li>2. To the address above</li>
                    <li>3. Payment will be confirmed automatically</li>
                    <li>4. Premium access activates immediately</li>
                  </ol>
                </div>
              </div>

              <!-- Success State -->
              <div v-else-if="payment?.payment_status === 'finished'" class="text-center">
                <div class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckIcon class="w-8 h-8 text-white" />
                </div>
                <h4 class="text-lg font-bold text-white mb-2">Payment Successful!</h4>
                <p class="text-gray-400 mb-4">Your premium subscription is now active.</p>
                
                <div class="bg-green-900/20 border border-green-700 rounded-lg p-4">
                  <h5 class="font-medium text-green-400 mb-2">Premium Features Unlocked</h5>
                  <ul class="text-sm text-gray-300 space-y-1">
                    <li>✓ Unlimited card generation</li>
                    <li>✓ AVS data with 7 countries</li>
                    <li>✓ Bulk generation up to 1000 cards</li>
                    <li>✓ Export in multiple formats</li>
                    <li>✓ Priority support</li>
                  </ul>
                </div>
              </div>

              <!-- Failed State -->
              <div v-else-if="payment?.payment_status === 'failed'" class="text-center">
                <div class="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ExclamationTriangleIcon class="w-8 h-8 text-white" />
                </div>
                <h4 class="text-lg font-bold text-white mb-2">Payment Failed</h4>
                <p class="text-gray-400 mb-4">The payment was not completed successfully.</p>
                
                <button @click="$emit('retry-payment')" class="btn btn-primary">
                  Try Again
                </button>
              </div>

              <!-- Expired State -->
              <div v-else-if="payment?.payment_status === 'expired'" class="text-center">
                <div class="w-16 h-16 bg-yellow-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ClockIcon class="w-8 h-8 text-white" />
                </div>
                <h4 class="text-lg font-bold text-white mb-2">Payment Expired</h4>
                <p class="text-gray-400 mb-4">The payment window has expired.</p>
                
                <button @click="$emit('retry-payment')" class="btn btn-primary">
                  Create New Payment
                </button>
              </div>
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-between p-6 border-t border-gray-700">
              <a 
                v-if="payment?.explorer_url" 
                :href="payment.explorer_url" 
                target="_blank"
                class="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                View on Explorer →
              </a>
              <div class="flex items-center space-x-3">
                <button @click="closeModal" class="btn btn-ghost">
                  Close
                </button>
                <button 
                  v-if="payment?.payment_status === 'waiting'"
                  @click="checkPaymentStatus" 
                  :disabled="isChecking"
                  class="btn btn-outline"
                >
                  <span v-if="isChecking">Checking...</span>
                  <span v-else>Check Status</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import QRCode from 'qrcode'
import { usePaymentStore } from '@/stores/payment'
import {
  XMarkIcon,
  DocumentDuplicateIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'

interface Props {
  show: boolean
  payment: any
}

interface Emits {
  (e: 'close'): void
  (e: 'retry-payment'): void
  (e: 'payment-completed'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Store
const paymentStore = usePaymentStore()

// Refs
const qrCodeElement = ref<HTMLElement>()
const isChecking = ref(false)
const timeRemaining = ref(0)
const timerInterval = ref<NodeJS.Timeout>()

// Computed
const paymentAddress = computed(() => props.payment?.pay_address || '')

// Methods
const closeModal = () => {
  emit('close')
  clearTimer()
}

const generateQRCode = async () => {
  if (!qrCodeElement.value || !paymentAddress.value) return
  
  try {
    const qrCodeData = `${props.payment?.pay_currency?.toLowerCase()}:${paymentAddress.value}?amount=${props.payment?.pay_amount}`
    qrCodeElement.value.innerHTML = ''
    await QRCode.toCanvas(qrCodeElement.value, qrCodeData, {
      width: 192,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    })
  } catch (error) {
    console.error('Failed to generate QR code:', error)
  }
}

const copyAddress = async () => {
  try {
    await navigator.clipboard.writeText(paymentAddress.value)
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'Payment address copied to clipboard',
    })
  } catch (error) {
    console.error('Failed to copy address:', error)
  }
}

const copyAmount = async () => {
  try {
    await navigator.clipboard.writeText(`${props.payment?.pay_amount}`)
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'Payment amount copied to clipboard',
    })
  } catch (error) {
    console.error('Failed to copy amount:', error)
  }
}

const checkPaymentStatus = async () => {
  if (!props.payment?.payment_id) return
  
  isChecking.value = true
  try {
    await paymentStore.checkPaymentStatus(props.payment.payment_id)
    
    // If payment is completed, emit event
    if (props.payment?.payment_status === 'finished') {
      emit('payment-completed')
    }
  } catch (error) {
    console.error('Failed to check payment status:', error)
  } finally {
    isChecking.value = false
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'waiting': return 'bg-yellow-900/20 text-yellow-400 border border-yellow-700'
    case 'confirming': return 'bg-blue-900/20 text-blue-400 border border-blue-700'
    case 'finished': return 'bg-green-900/20 text-green-400 border border-green-700'
    case 'failed': return 'bg-red-900/20 text-red-400 border border-red-700'
    case 'expired': return 'bg-gray-900/20 text-gray-400 border border-gray-700'
    default: return 'bg-gray-900/20 text-gray-400 border border-gray-700'
  }
}

const getStatusDotColor = (status: string) => {
  switch (status) {
    case 'waiting': return 'bg-yellow-400'
    case 'confirming': return 'bg-blue-400'
    case 'finished': return 'bg-green-400'
    case 'failed': return 'bg-red-400'
    case 'expired': return 'bg-gray-400'
    default: return 'bg-gray-400'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'waiting': return 'Waiting for Payment'
    case 'confirming': return 'Confirming Payment'
    case 'finished': return 'Payment Successful'
    case 'failed': return 'Payment Failed'
    case 'expired': return 'Payment Expired'
    default: return 'Unknown Status'
  }
}

const formatTime = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const startTimer = () => {
  if (!props.payment?.created_at || !props.payment?.valid_until) return
  
  const expiryTime = new Date(props.payment.valid_until).getTime()
  
  timerInterval.value = setInterval(() => {
    const now = Date.now()
    const remaining = Math.max(0, Math.floor((expiryTime - now) / 1000))
    timeRemaining.value = remaining
    
    if (remaining === 0) {
      clearTimer()
    }
  }, 1000)
}

const clearTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = undefined
  }
}

// Watchers
watch(() => props.payment, async (newPayment) => {
  if (newPayment && props.show) {
    await generateQRCode()
    
    if (newPayment.payment_status === 'waiting') {
      startTimer()
    }
  }
}, { immediate: true })

watch(() => props.show, (show) => {
  if (!show) {
    clearTimer()
  }
})

// Lifecycle
onMounted(() => {
  if (props.payment && props.show) {
    generateQRCode()
    if (props.payment.payment_status === 'waiting') {
      startTimer()
    }
  }
})

onUnmounted(() => {
  clearTimer()
})
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
</style>