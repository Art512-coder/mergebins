<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">Dashboard</h1>
      <p class="text-gray-400">Welcome back, {{ authStore.user?.username }}!</p>
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <!-- Plan Status -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="p-2 bg-primary-600/20 rounded-lg">
            <CreditCardIcon class="w-6 h-6 text-primary-400" />
          </div>
          <span :class="[
            'px-2 py-1 rounded-full text-xs font-medium',
            authStore.isPremium 
              ? 'bg-green-900/30 text-green-400' 
              : 'bg-gray-700 text-gray-300'
          ]">
            {{ authStore.user?.plan.toUpperCase() }}
          </span>
        </div>
        <div class="text-2xl font-bold text-white mb-1">
          {{ planDetails.title }}
        </div>
        <p class="text-gray-400 text-sm">{{ planDetails.description }}</p>
        <button
          v-if="!authStore.isPremium"
          @click="openUpgradeModal"
          class="mt-3 btn btn-primary w-full text-sm"
        >
          Upgrade Now
        </button>
      </div>

      <!-- Daily Usage -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="p-2 bg-secondary-600/20 rounded-lg">
            <ChartBarIcon class="w-6 h-6 text-secondary-400" />
          </div>
          <span class="text-sm text-gray-400">
            {{ usagePercentage }}% used
          </span>
        </div>
        <div class="text-2xl font-bold text-white mb-1">
          {{ usageStats?.daily_usage || 0 }}
        </div>
        <p class="text-gray-400 text-sm mb-3">
          of {{ usageStats?.daily_limit || 5 }} daily lookups
        </p>
        <!-- Progress bar -->
        <div class="w-full bg-gray-700 rounded-full h-2">
          <div
            :style="{ width: Math.min(usagePercentage, 100) + '%' }"
            :class="[
              'h-2 rounded-full transition-all duration-300',
              usagePercentage > 90 ? 'bg-red-500' : 
              usagePercentage > 70 ? 'bg-yellow-500' : 'bg-secondary-500'
            ]"
          ></div>
        </div>
      </div>

      <!-- Total Searches -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="p-2 bg-blue-600/20 rounded-lg">
            <MagnifyingGlassIcon class="w-6 h-6 text-blue-400" />
          </div>
        </div>
        <div class="text-2xl font-bold text-white mb-1">
          {{ usageStats?.total_usage || 0 }}
        </div>
        <p class="text-gray-400 text-sm">Total BIN lookups</p>
      </div>

      <!-- Generated Cards -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="p-2 bg-purple-600/20 rounded-lg">
            <CpuChipIcon class="w-6 h-6 text-purple-400" />
          </div>
        </div>
        <div class="text-2xl font-bold text-white mb-1">
          {{ generatedCardsCount }}
        </div>
        <p class="text-gray-400 text-sm">Cards generated</p>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <!-- Quick BIN Search -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
          <MagnifyingGlassIcon class="w-5 h-5 mr-2 text-primary-400" />
          Quick BIN Search
        </h3>
        <div class="space-y-3">
          <input
            v-model="quickSearchBin"
            @keyup.enter="performQuickSearch"
            type="text"
            placeholder="Enter BIN..."
            class="input text-sm"
            maxlength="8"
          />
          <button
            @click="performQuickSearch"
            :disabled="quickSearchBin.length < 6"
            class="btn btn-primary w-full text-sm"
          >
            Search
          </button>
        </div>
      </div>

      <!-- Quick Card Generation -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
          <CpuChipIcon class="w-5 h-5 mr-2 text-secondary-400" />
          Generate Cards
        </h3>
        <div class="space-y-3">
          <select v-model="quickGenCount" class="input text-sm">
            <option value="1">1 Card</option>
            <option value="5">5 Cards</option>
            <option value="10">10 Cards</option>
          </select>
          <button
            @click="generateQuickCards"
            :disabled="hasReachedDailyLimit"
            class="btn btn-primary w-full text-sm"
          >
            Generate
          </button>
        </div>
      </div>

      <!-- Account Actions -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
          <UserIcon class="w-5 h-5 mr-2 text-purple-400" />
          Account
        </h3>
        <div class="space-y-3">
          <router-link to="/subscription" class="btn btn-outline w-full text-sm">
            Manage Subscription
          </router-link>
          <button @click="exportData" class="btn btn-ghost w-full text-sm">
            Export Data
          </button>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid lg:grid-cols-2 gap-8">
      <!-- Recent Searches -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-white">Recent BIN Searches</h3>
          <router-link to="/lookup" class="text-primary-400 hover:text-primary-300 text-sm">
            View All
          </router-link>
        </div>
        
        <div v-if="recentSearches.length === 0" class="text-center py-8">
          <MagnifyingGlassIcon class="w-12 h-12 text-gray-600 mx-auto mb-2" />
          <p class="text-gray-500">No recent searches</p>
          <router-link to="/lookup" class="text-primary-400 hover:text-primary-300 text-sm">
            Start searching →
          </router-link>
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="search in recentSearches.slice(0, 5)"
            :key="search.id"
            class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg hover:bg-gray-900 transition-colors cursor-pointer"
            @click="navigateToSearch(search.bin)"
          >
            <div class="flex items-center space-x-3">
              <div class="font-mono text-primary-400 text-sm">{{ search.bin }}</div>
              <div class="text-sm text-gray-300">{{ search.result.brand }}</div>
              <div class="text-xs text-gray-500">{{ search.result.country }}</div>
            </div>
            <div class="text-xs text-gray-500">
              {{ formatTimeAgo(search.searched_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Chart -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-6">Usage Trends</h3>
        <div class="h-64 flex items-center justify-center">
          <!-- Placeholder for chart -->
          <div class="text-center">
            <ChartBarIcon class="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p class="text-gray-500 text-sm">Usage analytics coming soon</p>
          </div>
        </div>
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
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePaymentStore } from '@/stores/payment'
import { useBinSearch } from '@/composables/useBinSearch'
import { useCardGenerator } from '@/composables/useCardGenerator'
import { formatDate } from '@/utils/helpers'
import PaymentModal from '@/components/PaymentModal.vue'
import {
  CreditCardIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  UserIcon,
} from '@heroicons/vue/24/outline'

// Router
const router = useRouter()

// Stores
const authStore = useAuthStore()
const paymentStore = usePaymentStore()

// Composables
const { history: recentSearches, searchBIN } = useBinSearch()
const { generateCards } = useCardGenerator()

// Local state
const showPaymentModal = ref(false)
const quickSearchBin = ref('')
const quickGenCount = ref('1')
const generatedCardsCount = ref(0)

// Computed
const usageStats = computed(() => paymentStore.usageStats)

const planDetails = computed(() => {
  if (authStore.isPremium) {
    return {
      title: 'Premium Plan',
      description: 'Unlimited access to all features'
    }
  } else {
    const remaining = (usageStats.value?.daily_limit || 5) - (usageStats.value?.daily_usage || 0)
    return {
      title: 'Free Plan',
      description: `${remaining} lookups remaining today`
    }
  }
})

const usagePercentage = computed(() => {
  if (!usageStats.value) return 0
  return Math.round((usageStats.value.daily_usage / usageStats.value.daily_limit) * 100)
})

const hasReachedDailyLimit = computed(() => {
  return paymentStore.hasReachedDailyLimit
})

// Methods
const openUpgradeModal = () => {
  showPaymentModal.value = true
}

const performQuickSearch = async () => {
  if (quickSearchBin.value.length >= 6) {
    await searchBIN(quickSearchBin.value)
    router.push('/lookup')
  }
}

const generateQuickCards = async () => {
  await generateCards({ count: parseInt(quickGenCount.value) })
  generatedCardsCount.value += parseInt(quickGenCount.value)
  router.push('/generator')
}

const navigateToSearch = (bin: string) => {
  router.push(`/lookup?bin=${bin}`)
}

const exportData = async () => {
  // Mock export functionality
  window.addToast?.({
    type: 'info',
    title: 'Export started',
    message: 'Your data export will be ready shortly.',
  })
}

const onPaymentCreated = (payment: any) => {
  console.log('Payment created:', payment)
}

const formatTimeAgo = (date: string) => {
  const now = new Date()
  const searchDate = new Date(date)
  const diffInHours = Math.floor((now.getTime() - searchDate.getTime()) / (1000 * 60 * 60))
  
  if (diffInHours < 1) return 'Just now'
  if (diffInHours === 1) return '1 hour ago'
  if (diffInHours < 24) return `${diffInHours} hours ago`
  return formatDate(date)
}

// Lifecycle
onMounted(async () => {
  // Load user data and usage stats
  await Promise.all([
    paymentStore.loadUsageStats(),
    paymentStore.loadSubscription(),
  ])
})
</script>
