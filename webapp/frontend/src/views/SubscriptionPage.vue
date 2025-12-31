<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">Subscription</h1>
      <p class="text-gray-400">Manage your subscription and billing</p>
    </div>

    <!-- Current Plan -->
    <div class="card p-8 mb-8">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-white mb-2">Current Plan</h2>
          <div class="flex items-center space-x-4">
            <span :class="[
              'px-3 py-1 rounded-full text-sm font-medium',
              authStore.isPremium 
                ? 'bg-green-900/30 text-green-400' 
                : 'bg-gray-700 text-gray-300'
            ]">
              {{ authStore.user?.plan.toUpperCase() }}
            </span>
            <span v-if="subscription" class="text-gray-400 text-sm">
              {{ subscription.status === 'active' ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
        <div v-if="!authStore.isPremium" class="text-right">
          <button @click="openUpgradeModal" class="btn btn-primary">
            Upgrade to Premium
          </button>
        </div>
      </div>

      <!-- Plan Details -->
      <div class="grid md:grid-cols-2 gap-8">
        <div>
          <h3 class="font-semibold text-white mb-4">Plan Features</h3>
          <ul class="space-y-2">
            <li class="flex items-center text-gray-300">
              <CheckIcon v-if="authStore.isPremium" class="w-5 h-5 text-green-400 mr-3" />
              <XMarkIcon v-else class="w-5 h-5 text-gray-500 mr-3" />
              {{ authStore.isPremium ? 'Unlimited' : '3 daily' }} BIN lookups
            </li>
            <li class="flex items-center text-gray-300">
              <CheckIcon v-if="authStore.isPremium" class="w-5 h-5 text-green-400 mr-3" />
              <XMarkIcon v-else class="w-5 h-5 text-gray-500 mr-3" />
              {{ authStore.isPremium ? '5 daily + unlimited' : 'View-only' }} card generation
            </li>
            <li class="flex items-center text-gray-300">
              <CheckIcon v-if="authStore.isPremium" class="w-5 h-5 text-green-400 mr-3" />
              <XMarkIcon v-else class="w-5 h-5 text-gray-500 mr-3" />
              AVS (Address Verification) data
            </li>
            <li class="flex items-center text-gray-300">
              <CheckIcon v-if="authStore.isPremium" class="w-5 h-5 text-green-400 mr-3" />
              <XMarkIcon v-else class="w-5 h-5 text-gray-500 mr-3" />
              Bulk export (CSV, JSON)
            </li>
            <li class="flex items-center text-gray-300">
              <CheckIcon v-if="authStore.isPremium" class="w-5 h-5 text-green-400 mr-3" />
              <XMarkIcon v-else class="w-5 h-5 text-gray-500 mr-3" />
              Priority support
            </li>
          </ul>
        </div>

        <div v-if="subscription && authStore.isPremium">
          <h3 class="font-semibold text-white mb-4">Billing Information</h3>
          <div class="space-y-3">
            <div>
              <span class="text-gray-400 text-sm">Next billing date:</span>
              <div class="text-white">{{ formatDate(subscription.current_period_end) }}</div>
            </div>
            <div>
              <span class="text-gray-400 text-sm">Payment method:</span>
              <div class="text-white">{{ subscription.payment_method }}</div>
            </div>
            <div>
              <span class="text-gray-400 text-sm">Status:</span>
              <div class="text-white capitalize">{{ subscription.status }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Usage Statistics -->
    <div class="grid md:grid-cols-2 gap-8 mb-8">
      <!-- Daily Usage -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Daily Usage</h3>
        <div class="space-y-4">
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-gray-400 text-sm">BIN Lookups</span>
              <span class="text-white text-sm">
                {{ usageStats?.daily_usage || 0 }} / {{ authStore.isPremium ? 'Unlimited' : (usageStats?.daily_limit || 3) }}
              </span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-2">
              <div
                :style="{ width: Math.min(usagePercentage, 100) + '%' }"
                :class="[
                  'h-2 rounded-full transition-all duration-300',
                  usagePercentage > 90 ? 'bg-red-500' : 
                  usagePercentage > 70 ? 'bg-yellow-500' : 'bg-green-500'
                ]"
              ></div>
            </div>
          </div>
          
          <div class="text-center pt-4">
            <div class="text-2xl font-bold text-white">{{ usageStats?.total_usage || 0 }}</div>
            <div class="text-gray-400 text-sm">Total lookups</div>
          </div>
        </div>
      </div>

      <!-- Plan Comparison -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Plan Comparison</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-3 gap-4 text-sm">
            <div class="text-gray-400">Feature</div>
            <div class="text-center text-gray-400">Free</div>
            <div class="text-center text-gray-400">Premium</div>
          </div>
          
          <div class="grid grid-cols-3 gap-4 text-sm py-2 border-b border-gray-700">
            <div class="text-gray-300">Daily lookups</div>
            <div class="text-center text-gray-300">5</div>
            <div class="text-center text-green-400">Unlimited</div>
          </div>
          
          <div class="grid grid-cols-3 gap-4 text-sm py-2 border-b border-gray-700">
            <div class="text-gray-300">Card generation</div>
            <div class="text-center text-gray-500">Limited</div>
            <div class="text-center text-green-400">Unlimited</div>
          </div>
          
          <div class="grid grid-cols-3 gap-4 text-sm py-2 border-b border-gray-700">
            <div class="text-gray-300">AVS data</div>
            <div class="text-center text-gray-500">✗</div>
            <div class="text-center text-green-400">✓</div>
          </div>
          
          <div class="grid grid-cols-3 gap-4 text-sm py-2">
            <div class="text-gray-300">Bulk export</div>
            <div class="text-center text-gray-500">✗</div>
            <div class="text-center text-green-400">✓</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Payment History -->
    <div v-if="authStore.isPremium" class="card p-8">
      <h2 class="text-xl font-bold text-white mb-6">Payment History</h2>
      <div class="text-center py-8">
        <CreditCardIcon class="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <p class="text-gray-500">Payment history will appear here</p>
      </div>
    </div>

    <!-- Payment Modal -->
    <PaymentModal
      :show="showPaymentModal"
      tier="premium"
      @close="showPaymentModal = false"
      @payment-created="onPaymentCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usePaymentStore } from '@/stores/payment'
import { formatDate } from '@/utils/helpers'
import PaymentModal from '@/components/PaymentModal.vue'
import {
  CheckIcon,
  XMarkIcon,
  CreditCardIcon,
} from '@heroicons/vue/24/outline'

// Stores
const authStore = useAuthStore()
const paymentStore = usePaymentStore()

// Local state
const showPaymentModal = ref(false)

// Computed
const subscription = computed(() => paymentStore.subscription)
const usageStats = computed(() => paymentStore.usageStats)

const usagePercentage = computed(() => {
  if (!usageStats.value) return 0
  return Math.round((usageStats.value.daily_usage / usageStats.value.daily_limit) * 100)
})

// Methods
const openUpgradeModal = () => {
  showPaymentModal.value = true
}

const onPaymentCreated = (payment: any) => {
  console.log('Payment created:', payment)
  window.addToast?.({
    type: 'success',
    title: 'Payment initiated!',
    message: 'Complete your payment to upgrade to Premium.',
  })
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    paymentStore.loadSubscription(),
    paymentStore.loadUsageStats(),
  ])
})
</script>
