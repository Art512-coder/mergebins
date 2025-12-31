<template>
  <div class="max-w-2xl mx-auto">
    <!-- Search Input -->
    <div class="card p-4 sm:p-8">
      <div class="space-y-6">
        <div>
          <label for="bin-input" class="block text-sm font-medium text-gray-300 mb-2">
            Enter BIN (first 6-8 digits)
          </label>
          <div class="relative">
            <!-- Card brand indicator -->
            <div v-if="detectedBrand" class="absolute inset-y-0 left-0 flex items-center pl-3 z-10">
              <div :class="getBrandColor(detectedBrand)" class="px-2 py-1 rounded text-xs font-medium">
                {{ detectedBrand.toUpperCase() }}
              </div>
            </div>
            
            <input
              id="bin-input"
              v-model="displayQuery"
              @input="onInput"
              @keydown="onKeydown"
              @paste="onPaste"
              type="text"
              placeholder="e.g., 4111 1111"
              :class="['input text-lg pr-12', detectedBrand ? 'pl-20' : '']"
              maxlength="11"
              :disabled="isLoading"
            />
            
            <div class="absolute inset-y-0 right-0 flex items-center pr-3">
              <div v-if="isLoading" class="spinner"></div>
              <MagnifyingGlassIcon v-else class="w-5 h-5 text-gray-400" />
            </div>
          </div>
          
          <!-- Enhanced feedback -->
          <div class="mt-2 space-y-1">
            <p class="text-xs text-gray-500">
              Enter at least 6 digits for BIN lookup
            </p>
            <div v-if="validationMessage" class="text-xs" :class="getValidationColor()">
              {{ validationMessage }}
            </div>
          </div>
        </div>

        <!-- Real-time Results -->
        <transition name="fade" mode="out-in">
          <div v-if="isLoading" class="text-center py-8">
            <div class="spinner mx-auto mb-4"></div>
            <p class="text-gray-400">Searching BIN database...</p>
          </div>

          <div v-else-if="result" class="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 border border-gray-700 shadow-xl slide-up">
            <!-- Header with actions -->
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-primary-600/20 flex items-center justify-center">
                  <span class="text-primary-400 font-bold text-lg">{{ result.scheme?.charAt(0).toUpperCase() || 'B' }}</span>
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-white">BIN Information</h3>
                  <p class="text-gray-400 text-sm">{{ formatBIN(result.bin) }}</p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <button
                  @click="addToFavorites"
                  :class="[
                    'p-2 rounded-lg transition-all duration-200 hover:scale-105',
                    isFavorite(result.bin) 
                      ? 'text-yellow-400 bg-yellow-400/20 shadow-lg shadow-yellow-400/20' 
                      : 'text-gray-400 hover:text-yellow-400 hover:bg-yellow-400/10'
                  ]"
                  :title="isFavorite(result.bin) ? 'Remove from favorites' : 'Add to favorites'"
                >
                  <StarIcon :class="isFavorite(result.bin) ? 'fill-current' : ''" class="w-5 h-5" />
                </button>
                <button
                  @click="copyResult"
                  class="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-all duration-200 hover:scale-105"
                  title="Copy result"
                >
                  <DocumentDuplicateIcon class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- Status badge -->
            <div class="mb-4">
              <div :class="[
                'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                result.valid 
                  ? 'bg-green-400/20 text-green-400 border border-green-400/30' 
                  : 'bg-red-400/20 text-red-400 border border-red-400/30'
              ]">
                <div :class="[
                  'w-2 h-2 rounded-full mr-2',
                  result.valid ? 'bg-green-400' : 'bg-red-400'
                ]"></div>
                {{ result.valid ? 'Valid BIN' : 'Invalid BIN' }}
              </div>
            </div>

            <!-- Main info grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <!-- Primary info -->
              <div class="space-y-4">
                <div class="bg-gray-800/50 rounded-lg p-4 border border-gray-600/50">
                  <h4 class="text-gray-300 text-xs uppercase tracking-wider mb-3">Card Details</h4>
                  <div class="space-y-2">
                    <div class="flex justify-between items-center">
                      <span class="text-gray-400 text-sm">Scheme</span>
                      <span class="text-white font-semibold">{{ result.scheme || 'Unknown' }}</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-gray-400 text-sm">Brand</span>
                      <span class="text-white font-semibold">{{ result.brand || 'Unknown' }}</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-gray-400 text-sm">Type</span>
                      <span class="text-white">{{ result.type || 'Unknown' }}</span>
                    </div>
                    <div v-if="result.level" class="flex justify-between items-center">
                      <span class="text-gray-400 text-sm">Level</span>
                      <span class="text-white">{{ result.level }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Location & Bank info -->
              <div class="space-y-4">
                <div class="bg-gray-800/50 rounded-lg p-4 border border-gray-600/50">
                  <h4 class="text-gray-300 text-xs uppercase tracking-wider mb-3">Issuer Information</h4>
                  <div class="space-y-2">
                    <div class="flex justify-between items-center">
                      <span class="text-gray-400 text-sm">Country</span>
                      <div class="flex items-center space-x-2">
                        <span class="text-white">{{ result.country_name || result.country || 'Unknown' }}</span>
                        <span v-if="result.country_code" class="text-gray-500 text-xs">({{ result.country_code }})</span>
                      </div>
                    </div>
                    <div v-if="result.bank || result.bank_name || result.issuer" class="flex justify-between items-start">
                      <span class="text-gray-400 text-sm">Bank</span>
                      <div class="text-right">
                        <div class="text-white text-sm">{{ result.bank_name || result.bank || result.issuer || 'Unknown' }}</div>
                        <div v-if="result.bank_url" class="text-xs">
                          <a :href="result.bank_url" target="_blank" class="text-primary-400 hover:text-primary-300">
                            Visit Website
                          </a>
                        </div>
                        <div v-if="result.bank_phone" class="text-gray-500 text-xs">{{ result.bank_phone }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Additional info if available -->
            <div v-if="hasAdditionalInfo(result)" class="mt-4 p-3 bg-primary-600/10 border border-primary-600/20 rounded-lg">
              <p class="text-primary-300 text-sm flex items-center">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                </svg>
                Complete bank information available
              </p>
            </div>
          </div>

          <div v-else-if="error" class="bg-red-900/20 border border-red-700 rounded-lg p-4">
            <div class="flex items-center">
              <ExclamationTriangleIcon class="w-5 h-5 text-red-400 mr-2" />
              <p class="text-red-400">{{ error }}</p>
            </div>
          </div>

          <div v-else-if="query.length >= 6" class="text-center py-8">
            <MagnifyingGlassIcon class="w-12 h-12 text-gray-600 mx-auto mb-2" />
            <p class="text-gray-500">No results found for this BIN</p>
          </div>
        </transition>
      </div>
    </div>

    <!-- Search History -->
    <div v-if="history.length > 0" class="mt-8">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <h3 class="text-lg font-semibold text-white">Recent Searches</h3>
          <span class="bg-gray-700 text-gray-300 px-2 py-1 rounded-full text-xs">{{ history.length }}</span>
        </div>
        <div class="flex items-center space-x-3">
          <button 
            v-if="showAllHistory"
            @click="showAllHistory = false" 
            class="text-sm text-primary-400 hover:text-primary-300"
          >
            Show Less
          </button>
          <button 
            v-else-if="history.length > 5"
            @click="showAllHistory = true" 
            class="text-sm text-primary-400 hover:text-primary-300"
          >
            Show All ({{ history.length }})
          </button>
          <button @click="clearHistory" class="text-sm text-gray-400 hover:text-red-400 transition-colors">
            Clear All
          </button>
        </div>
      </div>
      
      <div class="space-y-3">
        <div
          v-for="item in (showAllHistory ? history : history.slice(0, 5))"
          :key="item.id"
          @click="searchBIN(item.bin)"
          class="group bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600 rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-lg"
        >
          <div class="flex items-center justify-between">
            <!-- Left side: BIN info -->
            <div class="flex items-center space-x-4">
              <!-- BIN number with brand indicator -->
              <div class="flex items-center space-x-2">
                <div class="font-mono text-lg text-primary-400 group-hover:text-primary-300">
                  {{ formatBIN(item.bin) }}
                </div>
                <div v-if="item.result.scheme" :class="getBrandColor(detectCardBrand(item.bin))" class="px-2 py-1 rounded text-xs font-medium">
                  {{ item.result.scheme.toUpperCase() }}
                </div>
              </div>
              
              <!-- Card details -->
              <div class="hidden sm:flex items-center space-x-4 text-sm">
                <div class="flex items-center space-x-1">
                  <span class="text-gray-500">Brand:</span>
                  <span class="text-gray-300 font-medium">{{ item.result.brand || 'Unknown' }}</span>
                </div>
                <div class="flex items-center space-x-1">
                  <span class="text-gray-500">Country:</span>
                  <span class="text-gray-300">{{ item.result.country || 'Unknown' }}</span>
                </div>
                <div class="flex items-center space-x-1">
                  <span class="text-gray-500">Type:</span>
                  <span class="text-gray-300">{{ item.result.type || 'Unknown' }}</span>
                </div>
              </div>
            </div>

            <!-- Right side: Actions and timestamp -->
            <div class="flex items-center space-x-3">
              <!-- Quick actions -->
              <div class="hidden group-hover:flex items-center space-x-2">
                <button
                  @click.stop="toggleHistoryFavorite(item.bin)"
                  :class="[
                    'p-1 rounded transition-colors',
                    isFavorite(item.bin) 
                      ? 'text-yellow-400' 
                      : 'text-gray-500 hover:text-yellow-400'
                  ]"
                >
                  <StarIcon :class="isFavorite(item.bin) ? 'fill-current' : ''" class="w-4 h-4" />
                </button>
                <button
                  @click.stop="copyHistoryResult(item)"
                  class="p-1 rounded text-gray-500 hover:text-gray-300 transition-colors"
                >
                  <DocumentDuplicateIcon class="w-4 h-4" />
                </button>
              </div>
              
              <!-- Timestamp -->
              <div class="text-xs text-gray-500 whitespace-nowrap">
                {{ formatDate(item.searched_at) }}
              </div>
            </div>
          </div>
          
          <!-- Mobile: Show details on separate line -->
          <div class="sm:hidden mt-2 flex items-center space-x-4 text-sm">
            <span class="text-gray-400">{{ item.result.brand || 'Unknown' }}</span>
            <span class="text-gray-500">•</span>
            <span class="text-gray-400">{{ item.result.country || 'Unknown' }}</span>
            <span class="text-gray-500">•</span>
            <span class="text-gray-400">{{ item.result.type || 'Unknown' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Favorites -->
    <div v-if="favorites.length > 0" class="mt-8">
      <h3 class="text-lg font-semibold text-white mb-4">Favorite BINs</h3>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="bin in favorites"
          :key="bin"
          @click="searchBIN(bin)"
          class="px-3 py-1 bg-yellow-400/10 text-yellow-400 rounded-full text-sm hover:bg-yellow-400/20 transition-colors"
        >
          {{ bin }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useBinSearch } from '@/composables/useBinSearch'
import { useDebounceFunction } from '@/composables/useDebounce'
import { formatDate, copyToClipboard } from '@/utils/helpers'
import {
  MagnifyingGlassIcon,
  StarIcon,
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

// Use the BIN search composable
const {
  query,
  result,
  history,
  favorites,
  isLoading,
  error,
  // isValidBIN,
  searchBIN,
  addToFavorites: addToFav,
  removeFromFavorites,
  isFavorite,
  clearHistory,
} = useBinSearch()

// Local reactive data for formatting
const displayQuery = ref('')
const detectedBrand = ref('')
const validationMessage = ref('')
const showAllHistory = ref(false)

// Debounced search function
const { debouncedFunction: debouncedSearch } = useDebounceFunction(
  (bin: string) => searchBIN(bin), 
  500
)

// Card brand detection patterns
const brandPatterns = {
  visa: /^4/,
  mastercard: /^(5[1-5]|2[2-7])/,
  amex: /^3[47]/,
  discover: /^6(?:011|5)/,
  diners: /^3[0689]/,
  jcb: /^35/
}

// Methods
const detectCardBrand = (digits: string) => {
  for (const [brand, pattern] of Object.entries(brandPatterns)) {
    if (pattern.test(digits)) {
      return brand
    }
  }
  return ''
}

const getBrandColor = (brand: string) => {
  const colors: Record<string, string> = {
    visa: 'bg-blue-600 text-white',
    mastercard: 'bg-red-600 text-white',
    amex: 'bg-green-600 text-white',
    discover: 'bg-orange-600 text-white',
    diners: 'bg-purple-600 text-white',
    jcb: 'bg-indigo-600 text-white'
  }
  return colors[brand] || 'bg-gray-600 text-white'
}

const formatBIN = (value: string) => {
  // Remove all non-digits
  const digits = value.replace(/\D/g, '')
  // Add spaces every 4 digits
  return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim()
}

const getValidationColor = () => {
  const rawDigits = query.value
  if (rawDigits.length === 0) return 'text-gray-500'
  if (rawDigits.length < 6) return 'text-yellow-400'
  return 'text-green-400'
}

const updateValidationMessage = (digits: string) => {
  if (digits.length === 0) {
    validationMessage.value = ''
  } else if (digits.length < 6) {
    validationMessage.value = `Need ${6 - digits.length} more digit${6 - digits.length === 1 ? '' : 's'}`
  } else {
    validationMessage.value = 'Ready to search!'
  }
}

const onInput = (event: Event) => {
  const input = event.target as HTMLInputElement
  const rawValue = input.value.replace(/\D/g, '') // Extract only digits
  
  // Limit to 8 digits
  const limitedValue = rawValue.slice(0, 8)
  
  // Update the actual query (digits only)
  query.value = limitedValue
  
  // Update the formatted display
  displayQuery.value = formatBIN(limitedValue)
  
  // Detect brand
  detectedBrand.value = detectCardBrand(limitedValue)
  
  // Update validation message
  updateValidationMessage(limitedValue)
  
  // Search if enough digits
  if (limitedValue.length >= 6) {
    debouncedSearch(limitedValue)
  } else {
    result.value = null
    error.value = null
  }
}

const onKeydown = (event: KeyboardEvent) => {
  // Allow backspace, delete, tab, escape, enter
  if ([8, 9, 27, 13, 46].indexOf(event.keyCode) !== -1 ||
      // Allow Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
      (event.keyCode === 65 && event.ctrlKey === true) ||
      (event.keyCode === 67 && event.ctrlKey === true) ||
      (event.keyCode === 86 && event.ctrlKey === true) ||
      (event.keyCode === 88 && event.ctrlKey === true)) {
    return
  }
  // Ensure that it's a number
  if ((event.shiftKey || (event.keyCode < 48 || event.keyCode > 57)) && (event.keyCode < 96 || event.keyCode > 105)) {
    event.preventDefault()
  }
}

const onPaste = (event: ClipboardEvent) => {
  event.preventDefault()
  const paste = event.clipboardData?.getData('text') || ''
  const digits = paste.replace(/\D/g, '').slice(0, 8)
  
  query.value = digits
  displayQuery.value = formatBIN(digits)
  detectedBrand.value = detectCardBrand(digits)
  updateValidationMessage(digits)
  
  if (digits.length >= 6) {
    debouncedSearch(digits)
  }
}

const hasAdditionalInfo = (result: any) => {
  return result.bank_url || result.bank_phone || result.level || result.country_code
}

const toggleHistoryFavorite = (bin: string) => {
  if (isFavorite(bin)) {
    removeFromFavorites(bin)
  } else {
    addToFav(bin)
  }
}

const copyHistoryResult = async (item: any) => {
  const text = `BIN: ${item.bin}\nScheme: ${item.result.scheme}\nType: ${item.result.type}\nBrand: ${item.result.brand}\nCountry: ${item.result.country}`
  
  const success = await copyToClipboard(text)
  if (success) {
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'BIN information copied to clipboard.',
    })
  }
}

const addToFavorites = () => {
  if (result.value) {
    if (isFavorite(result.value.bin)) {
      removeFromFavorites(result.value.bin)
    } else {
      addToFav(result.value.bin)
    }
  }
}

const copyResult = async () => {
  if (!result.value) return
  
  const text = `BIN: ${result.value.bin}\nScheme: ${result.value.scheme}\nType: ${result.value.type}\nBrand: ${result.value.brand}\nCountry: ${result.value.country}`
  
  const success = await copyToClipboard(text)
  if (success) {
    window.addToast?.({
      type: 'success',
      title: 'Copied!',
      message: 'BIN information copied to clipboard.',
    })
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
