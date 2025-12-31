<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-white mb-2">Card Generator</h1>
          <p class="text-gray-400">Generate realistic credit card numbers for testing purposes</p>
        </div>
        <div class="text-right">
          <p class="text-sm text-gray-400 mb-2">Also available on Telegram:</p>
          <a 
            href="https://t.me/BINSearchCCGBot" 
            target="_blank"
            class="inline-flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
          >
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
            </svg>
            @BINSearchCCGBot
          </a>
        </div>
      </div>
    </div>

    <!-- Generation Controls -->
    <div class="card p-8 mb-8">
      <form @submit.prevent="handleGenerate" class="space-y-6">
        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Number of Cards -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">
              Number of Cards
            </label>
            <select v-model="form.count" class="input" :disabled="isLoading">
              <option value="1">1 Card</option>
              <option value="5">5 Cards</option>
              <option value="10">10 Cards</option>
              <option value="25" :disabled="!authStore.isPremium">25 Cards {{ !authStore.isPremium ? '(Premium)' : '' }}</option>
              <option value="50" :disabled="!authStore.isPremium">50 Cards {{ !authStore.isPremium ? '(Premium)' : '' }}</option>
              <option value="100" :disabled="!authStore.isPremium">100 Cards {{ !authStore.isPremium ? '(Premium)' : '' }}</option>
              <option value="250" :disabled="!authStore.isPremium">250 Cards {{ !authStore.isPremium ? '(Premium)' : '' }}</option>
              <option value="500" :disabled="!authStore.isPremium">500 Cards {{ !authStore.isPremium ? '(Premium)' : '' }}</option>
              <option value="1000" :disabled="!authStore.isPremium">1000 Cards {{ !authStore.isPremium ? '(Premium)' : '' }}</option>
            </select>
          </div>

          <!-- BIN (Optional) -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">
              BIN (Optional)
            </label>
            <input
              v-model="form.bin"
              type="text"
              placeholder="e.g., 411111"
              class="input"
              maxlength="8"
              :disabled="isLoading"
              @input="validateBIN"
            />
            <div class="text-xs mt-1">
              <p class="text-gray-500">Leave empty for random BIN</p>
              <div v-if="binSuggestions.length > 0" class="mt-1">
                <p class="text-gray-400 mb-1">Popular BINs:</p>
                <div class="flex flex-wrap gap-1">
                  <button
                    v-for="suggestion in binSuggestions"
                    :key="suggestion.bin"
                    @click="form.bin = suggestion.bin"
                    class="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition-colors"
                    type="button"
                  >
                    {{ suggestion.bin }} ({{ suggestion.brand }})
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Include AVS -->
          <div>
            <label class="flex items-center cursor-pointer mb-3">
              <input
                v-model="form.include_avs"
                type="checkbox"
                class="sr-only"
                :disabled="isLoading || !authStore.isPremium"
              />
              <div :class="[
                'relative w-5 h-5 rounded border-2 transition-colors',
                form.include_avs && authStore.isPremium
                  ? 'bg-primary-600 border-primary-600'
                  : 'border-gray-600'
              ]">
                <CheckIcon v-if="form.include_avs && authStore.isPremium" class="w-3 h-3 text-white absolute top-0.5 left-0.5" />
              </div>
              <span class="ml-2 text-sm text-gray-300">Include AVS Data</span>
              <span v-if="!authStore.isPremium" class="ml-2 text-xs bg-yellow-600 text-yellow-100 px-2 py-0.5 rounded-full">
                Premium
              </span>
            </label>
            
            <!-- AVS Country Selection -->
            <div v-if="form.include_avs && authStore.isPremium">
              <label class="block text-sm font-medium text-gray-300 mb-2">
                AVS Country
              </label>
              <select v-model="form.avs_country" class="input" :disabled="isLoading">
                <option value="US">🇺🇸 United States</option>
                <option value="IT">🇮🇹 Italy</option>
                <option value="GB">🇬🇧 United Kingdom</option>
                <option value="CA">🇨🇦 Canada</option>
                <option value="AU">🇦🇺 Australia</option>
                <option value="DE">🇩🇪 Germany</option>
                <option value="FR">🇫🇷 France</option>
              </select>
            </div>
          </div>

          <!-- Generate Button -->
          <div class="flex items-end">
            <button
              type="submit"
              :disabled="isLoading || hasReachedLimit"
              class="btn btn-primary w-full"
            >
              <div v-if="isLoading" class="flex items-center justify-center">
                <div class="spinner mr-2"></div>
                Generating...
              </div>
              <span v-else>Generate Cards</span>
            </button>
          </div>
        </div>

        <!-- Usage Warning -->
        <div v-if="hasReachedLimit" class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
          <div class="flex items-center">
            <ExclamationTriangleIcon class="w-5 h-5 text-yellow-400 mr-2" />
            <p class="text-yellow-400 text-sm">
              You've reached your daily limit. 
              <button @click="openUpgradeModal" class="underline hover:no-underline">
                Upgrade to Premium
              </button> for unlimited generation.
            </p>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div class="flex items-center">
            <ExclamationTriangleIcon class="w-5 h-5 text-red-400 mr-2" />
            <p class="text-red-400 text-sm">{{ error }}</p>
          </div>
        </div>
      </form>
    </div>

    <!-- Generated Cards -->
    <div v-if="cards.length > 0" class="space-y-6">
      <!-- Export Controls -->
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-bold text-white">
          Generated Cards ({{ cards.length }})
        </h2>
        <div class="flex items-center space-x-3">
          <button @click="copyAllCards" class="btn btn-ghost text-sm">
            <DocumentDuplicateIcon class="w-4 h-4 mr-2" />
            Copy All
          </button>
          <div class="relative">
            <button
              @click="showExportMenu = !showExportMenu"
              class="btn btn-outline text-sm"
            >
              <ArrowDownTrayIcon class="w-4 h-4 mr-2" />
              Export
              <ChevronDownIcon class="w-4 h-4 ml-2" />
            </button>
            
            <!-- Export Dropdown -->
            <div v-show="showExportMenu" class="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-1 z-10">
              <button
                v-for="format in exportFormats"
                :key="format.value"
                @click="exportCards(format.value as 'json' | 'csv' | 'txt')"
                class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
              >
                {{ format.label }}
              </button>
            </div>
          </div>
          <button @click="clearCards" class="btn btn-ghost text-sm text-red-400 hover:text-red-300">
            Clear All
          </button>
        </div>
      </div>

      <!-- Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <transition-group name="card" appear>
          <CardDisplay
            v-for="(card, index) in cards"
            :key="`${card.number}-${index}`"
            :card="card"
            class="card-item"
            :style="{ '--delay': index * 100 + 'ms' }"
          />
        </transition-group>
      </div>

      <!-- Bulk Actions -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Bulk Actions</h3>
        <div class="grid md:grid-cols-3 gap-4">
          <button @click="copyNumbers" class="btn btn-outline text-sm">
            Copy Numbers Only
          </button>
          <button @click="copyWithCVV" class="btn btn-outline text-sm">
            Copy Numbers + CVV
          </button>
          <button @click="copyFullDetails" class="btn btn-outline text-sm">
            Copy Full Details
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-16">
      <CpuChipIcon class="w-16 h-16 text-gray-600 mx-auto mb-4" />
      <h3 class="text-xl font-semibold text-white mb-2">No Cards Generated Yet</h3>
      <p class="text-gray-400 mb-6">Generate your first batch of test cards using the form above</p>
      <div class="flex flex-wrap justify-center gap-2">
        <button
          v-for="quickCount in authStore.isPremium ? [1, 5, 10, 25, 50] : [1, 5]"
          :key="quickCount"
          @click="quickGenerate(quickCount)"
          :disabled="hasReachedLimit"
          class="btn btn-outline text-sm"
        >
          Generate {{ quickCount }} Card{{ quickCount > 1 ? 's' : '' }}
          <span v-if="quickCount > 10 && !authStore.isPremium" class="ml-1 text-xs bg-yellow-600 text-yellow-100 px-1 py-0.5 rounded">
            Premium
          </span>
        </button>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usePaymentStore } from '@/stores/payment'
import { useCardGenerator } from '@/composables/useCardGenerator'
import { copyToClipboard } from '@/utils/helpers'
import CardDisplay from '@/components/CardDisplay.vue'
import PaymentModal from '@/components/PaymentModal.vue'
import {
  CheckIcon,
  ExclamationTriangleIcon,
  DocumentDuplicateIcon,
  ArrowDownTrayIcon,
  ChevronDownIcon,
  CpuChipIcon,
} from '@heroicons/vue/24/outline'

// Stores
const authStore = useAuthStore()
const paymentStore = usePaymentStore()

// Composables
const {
  cards,
  isLoading,
  error,
  generateCards,
  exportCards: exportCardsFile,
  clearCards,
  // copyCard,
  copyAllCards: copyAll,
} = useCardGenerator()

// Local state
const form = ref({
  count: 5,
  bin: '',
  include_avs: false,
  avs_country: 'US',
})

const showExportMenu = ref(false)
const showPaymentModal = ref(false)
const binSuggestions = ref([
  { bin: '411111', brand: 'VISA' },
  { bin: '524542', brand: 'MASTERCARD' },
  { bin: '378282', brand: 'AMEX' },
  { bin: '6011000', brand: 'DISCOVER' },
  { bin: '4000000', brand: 'VISA' },
])

const exportFormats = [
  { value: 'json', label: 'JSON Format' },
  { value: 'csv', label: 'CSV Format' },
  { value: 'txt', label: 'Plain Text' },
]

// Computed
const hasReachedLimit = computed(() => {
  return !authStore.isPremium && paymentStore.hasReachedDailyLimit
})

// Methods
const handleGenerate = async () => {
  if (hasReachedLimit.value) return

  await generateCards({
    count: form.value.count,
    bin: form.value.bin || undefined,
    include_avs: form.value.include_avs && authStore.isPremium,
    country_code: form.value.avs_country,
    format: 'json',
  })
}

const quickGenerate = async (count: number) => {
  form.value.count = count
  await handleGenerate()
}

const openUpgradeModal = () => {
  showPaymentModal.value = true
}

const exportCards = async (format: 'json' | 'csv' | 'txt') => {
  showExportMenu.value = false
  await exportCardsFile(format)
}

const copyNumbers = async () => {
  const numbers = cards.value.map(card => card.number).join('\n')
  const success = await copyToClipboard(numbers)
  if (success) {
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'Card numbers copied to clipboard.',
    })
  }
}

const copyWithCVV = async () => {
  const cardsText = cards.value
    .map(card => `${card.number} | ${card.cvv}`)
    .join('\n')
  const success = await copyToClipboard(cardsText)
  if (success) {
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'Card numbers and CVVs copied to clipboard.',
    })
  }
}

const copyFullDetails = async () => {
  const cardsText = cards.value
    .map(card => `${card.number} | ${card.cvv} | ${card.expiry} | ${card.brand}`)
    .join('\n')
  const success = await copyToClipboard(cardsText)
  if (success) {
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'Full card details copied to clipboard.',
    })
  }
}

const copyAllCards = async () => {
  await copyAll()
}

const validateBIN = () => {
  const bin = form.value.bin
  if (bin && (bin.length < 4 || bin.length > 8 || !/^\d+$/.test(bin))) {
    // Could add visual feedback for invalid BIN
  }
}

const onPaymentCreated = (payment: any) => {
  console.log('Payment created:', payment)
  // Refresh user status to get updated premium state
  authStore.refreshUser()
}

// Global click handler to close menus
const handleGlobalClick = (event: Event) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    showExportMenu.value = false
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleGlobalClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
})
</script>

<style scoped>
.card-enter-active {
  transition: all 0.6s ease;
  transition-delay: var(--delay);
}

.card-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.9);
}

.card-item {
  animation: cardAppear 0.6s ease forwards;
  animation-delay: var(--delay);
  opacity: 0;
}

@keyframes cardAppear {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
