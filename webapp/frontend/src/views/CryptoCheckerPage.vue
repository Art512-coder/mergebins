<template>
  <div class="min-h-screen bg-gray-950 py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-12">
        <h1 class="text-4xl font-bold text-white mb-4">
          <span class="text-gradient">Crypto Wallet</span> Balance Checker
        </h1>
        <p class="text-xl text-gray-300 max-w-2xl mx-auto">
          Check Bitcoin and Ethereum wallet balances instantly. 
          Verify wallet activity and transaction history for fraud prevention.
        </p>
      </div>

      <!-- Main Card -->
      <div class="card p-8 mb-8">
        <!-- Input Section -->
        <div class="mb-8">
          <div class="flex flex-col md:flex-row gap-4 mb-6">
            <!-- Crypto Type Selector -->
            <div class="md:w-1/3">
              <label for="crypto-type" class="block text-sm font-medium text-gray-300 mb-2">
                Cryptocurrency
              </label>
              <select v-model="selectedCrypto" 
                      id="crypto-type"
                      class="input-field">
                <option value="bitcoin">Bitcoin (BTC)</option>
                <option value="ethereum">Ethereum (ETH)</option>
                <option value="litecoin">Litecoin (LTC)</option>
                <option value="dogecoin">Dogecoin (DOGE)</option>
                <option value="cardano">Cardano (ADA)</option>
                <option value="solana">Solana (SOL)</option>
              </select>
            </div>

            <!-- Wallet Address Input -->
            <div class="md:w-2/3">
              <label for="wallet-address" class="block text-sm font-medium text-gray-300 mb-2">
                Wallet Address
              </label>
              <input v-model="walletAddress" 
                     @keyup.enter="checkBalance"
                     id="wallet-address"
                     type="text" 
                     :placeholder="getPlaceholderText()"
                     class="input-field">
            </div>
          </div>

          <!-- Check Button -->
          <div class="flex justify-center">
            <button @click="checkBalance" 
                    :disabled="!walletAddress || isLoading"
                    class="btn btn-primary px-8 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed">
              <span v-if="isLoading" class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Checking...
              </span>
              <span v-else>Check Balance</span>
            </button>
          </div>
        </div>

        <!-- Results Section -->
        <div v-if="result" class="border-t border-gray-700 pt-8">
          <div v-if="result.success" class="space-y-6">
            <!-- Balance Card -->
            <div class="bg-gradient-to-r from-green-600/20 to-emerald-600/20 border border-green-500/30 rounded-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-xl font-semibold text-white">Wallet Balance</h3>
                <div class="text-sm text-gray-400">
                  {{ new Date(result.data.timestamp).toLocaleString() }}
                </div>
              </div>
              
              <div class="grid md:grid-cols-2 gap-6">
                <div>
                  <div class="text-3xl font-bold text-green-400 mb-1">
                    {{ result.data.balance }} {{ selectedCrypto.toUpperCase() }}
                  </div>
                  <div class="text-gray-400">Current Balance</div>
                </div>
                <div>
                  <div class="text-3xl font-bold text-white mb-1">
                    ${{ result.data.usd_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                  </div>
                  <div class="text-gray-400">USD Value</div>
                </div>
              </div>
              
              <div class="mt-4 text-sm text-gray-300">
                Current Price: ${{ result.data.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }} per {{ selectedCrypto.toUpperCase() }}
              </div>
            </div>

            <!-- Wallet Info -->
            <div class="bg-gray-800/50 rounded-lg p-6">
              <h3 class="text-lg font-semibold text-white mb-4">Wallet Information</h3>
              <div class="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-400">Address:</span>
                  <div class="text-white font-mono break-all">{{ walletAddress }}</div>
                </div>
                <div>
                  <span class="text-gray-400">Type:</span>
                  <div class="text-white">{{ getCryptoDisplayName() }} Wallet</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Error State -->
          <div v-else class="bg-red-600/20 border border-red-500/30 rounded-lg p-6">
            <div class="flex items-center space-x-3">
              <ExclamationTriangleIcon class="w-6 h-6 text-red-400" />
              <div>
                <h3 class="text-lg font-semibold text-red-400">Error</h3>
                <p class="text-gray-300">{{ result.error }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Features Section -->
      <div class="grid md:grid-cols-3 gap-6 mb-8">
        <div class="card p-6 text-center">
          <div class="w-12 h-12 bg-primary-600 rounded-lg flex items-center justify-center mx-auto mb-4">
            <BoltIcon class="w-6 h-6 text-white" />
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Real-time Data</h3>
          <p class="text-gray-400 text-sm">Get up-to-date balance and price information from multiple blockchain APIs.</p>
        </div>

        <div class="card p-6 text-center">
          <div class="w-12 h-12 bg-secondary-600 rounded-lg flex items-center justify-center mx-auto mb-4">
            <ShieldCheckIcon class="w-6 h-6 text-white" />
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Secure & Private</h3>
          <p class="text-gray-400 text-sm">No wallet data is stored. All requests are processed securely and anonymously.</p>
        </div>

        <div class="card p-6 text-center">
          <div class="w-12 h-12 bg-primary-600 rounded-lg flex items-center justify-center mx-auto mb-4">
            <CurrencyDollarIcon class="w-6 h-6 text-white" />
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">Multi-Currency</h3>
          <p class="text-gray-400 text-sm">Support for Bitcoin, Ethereum, and other major cryptocurrencies.</p>
        </div>
      </div>

      <!-- Premium Features -->
      <div v-if="!authStore.isPremium" class="card p-6 border-yellow-500/30 bg-yellow-600/10">
        <div class="text-center">
          <h3 class="text-xl font-semibold text-yellow-400 mb-3">🔓 Unlock Premium Features</h3>
          <p class="text-gray-300 mb-4">
            Premium users get unlimited wallet checks, batch processing, and historical data analysis.
          </p>
          <router-link to="/subscription" class="btn btn-primary">
            Upgrade to Premium
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/utils/api'
import {
  ExclamationTriangleIcon,
  BoltIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon
} from '@heroicons/vue/24/outline'

// Stores
const authStore = useAuthStore()

// State
const selectedCrypto = ref('bitcoin')
const walletAddress = ref('')
const isLoading = ref(false)
const result = ref<any>(null)

// Methods
const getPlaceholderText = () => {
  const placeholders = {
    bitcoin: 'Enter Bitcoin address (e.g., 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa)',
    ethereum: 'Enter Ethereum address (e.g., 0x742d35Cc6aB3BfEfD1f3A1d3F6D8B1E9C2A8F4B5)',
    litecoin: 'Enter Litecoin address (e.g., LX2m2f6LfNjzBF9E...)',
    dogecoin: 'Enter Dogecoin address (e.g., D8x2f6LfNjzBF9E...)',
    cardano: 'Enter Cardano address (e.g., addr1q...)',
    solana: 'Enter Solana address (e.g., 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM)'
  }
  return placeholders[selectedCrypto.value] || 'Enter wallet address'
}

const getCryptoDisplayName = () => {
  const names = {
    bitcoin: 'Bitcoin',
    ethereum: 'Ethereum', 
    litecoin: 'Litecoin',
    dogecoin: 'Dogecoin',
    cardano: 'Cardano',
    solana: 'Solana'
  }
  return names[selectedCrypto.value] || selectedCrypto.value
}

const checkBalance = async () => {
  if (!walletAddress.value) return
  
  isLoading.value = true
  result.value = null
  
  try {
    const response = await apiClient.post('/crypto/check-balance', {
      crypto_type: selectedCrypto.value,
      address: walletAddress.value
    })
    
    result.value = {
      success: true,
      data: response
    }
  } catch (error: any) {
    result.value = {
      success: false,
      error: error.response?.data?.detail || 'Failed to check wallet balance. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>
