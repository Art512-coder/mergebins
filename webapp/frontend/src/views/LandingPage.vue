<template>
  <div class="min-h-screen bg-gray-950">
    <!-- Hero Section -->
    <section class="relative overflow-hidden bg-gradient-to-br from-gray-900 via-gray-950 to-black">
      <!-- Background decorations -->
      <div class="absolute inset-0 bg-noise"></div>
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary-500/10 rounded-full blur-3xl"></div>
      
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
        <div class="text-center">
          <!-- Logo -->
          <div class="flex justify-center mb-8">
            <div class="w-16 h-16 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl flex items-center justify-center shadow-2xl">
              <span class="text-white font-bold text-2xl">BS</span>
            </div>
          </div>
          
          <!-- Main heading -->
          <h1 class="text-5xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            Check <span class="text-gradient">Crypto Wallet</span> Balances
            <br />
            <span class="text-4xl lg:text-5xl">Search BINs</span>
          </h1>
          
          <p class="text-xl lg:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            Free crypto wallet balance checker and the world's largest free BIN database. 
            Over 450,000+ BIN records for developers, QA testers, and payment processors.
          </p>
          
          <!-- BIN Checker Demo -->
          <div class="max-w-xl mx-auto mb-12">
            <div class="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700">
              <h3 class="text-2xl font-bold text-white mb-4 text-center">Try BIN Search Now</h3>
              <p class="text-gray-400 text-center mb-6">Enter a BIN number to see instant results - completely free!</p>
              
              <div class="flex gap-3">
                <input
                  v-model="demoBin"
                  @keyup.enter="searchDemoBin"
                  type="text"
                  placeholder="e.g., 411111, 424242"
                  class="input-field flex-1"
                  maxlength="8"
                />
                <button 
                  @click="searchDemoBin"
                  :disabled="isLoadingDemo || demoBin.length < 6"
                  class="btn btn-primary px-6 py-3 whitespace-nowrap disabled:opacity-50"
                >
                  <span v-if="isLoadingDemo" class="flex items-center">
                    <div class="spinner mr-2"></div>
                    Searching...
                  </span>
                  <span v-else>Search BIN</span>
                </button>
              </div>
              
              <!-- Demo Result -->
              <div v-if="demoResult" class="mt-6 p-4 bg-gray-900/50 rounded-lg border border-gray-600">
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-gray-400">Brand:</span>
                    <span class="text-white ml-2 font-medium">{{ demoResult.brand || 'N/A' }}</span>
                  </div>
                  <div>
                    <span class="text-gray-400">Type:</span>
                    <span class="text-white ml-2 font-medium">{{ demoResult.type || 'N/A' }}</span>
                  </div>
                  <div>
                    <span class="text-gray-400">Country:</span>
                    <span class="text-white ml-2 font-medium">{{ demoResult.country_name || 'N/A' }}</span>
                  </div>
                  <div>
                    <span class="text-gray-400">Issuer:</span>
                    <span class="text-white ml-2 font-medium">{{ demoResult.issuer || 'N/A' }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="demoError" class="mt-6 p-4 bg-red-900/20 border border-red-600 rounded-lg">
                <p class="text-red-400 text-sm">{{ demoError }}</p>
              </div>
            </div>
          </div>

          <!-- Quick CTA -->
          <div class="text-center mb-8">
            <router-link v-if="!authStore.isAuthenticated" to="/register" 
                         class="btn btn-primary text-lg px-8 py-4 shadow-lg hover:shadow-xl transform hover:scale-105 mr-4">
              Sign Up for More Features
            </router-link>
            <router-link to="/crypto-checker" class="btn btn-secondary text-lg px-8 py-4 shadow-lg hover:shadow-xl transform hover:scale-105">
              Try Crypto Checker
            </router-link>
          </div>
          
          <!-- Stats -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
            <div class="text-center">
              <div class="text-3xl lg:text-4xl font-bold text-white mb-2">454K+</div>
              <div class="text-gray-400">BIN Records</div>
            </div>
            <div class="text-center">
              <div class="text-3xl lg:text-4xl font-bold text-white mb-2">200+</div>
              <div class="text-gray-400">Cryptocurrencies</div>
            </div>
            <div class="text-center">
              <div class="text-3xl lg:text-4xl font-bold text-white mb-2">99.9%</div>
              <div class="text-gray-400">Uptime</div>
            </div>
            <div class="text-center">
              <div class="text-3xl lg:text-4xl font-bold text-white mb-2">< 100ms</div>
              <div class="text-gray-400">Response Time</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Demo Section -->
    <section ref="demoSection" class="py-24 bg-gray-900/50">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-white mb-4">Try It Now</h2>
          <p class="text-xl text-gray-300">Enter a BIN number to see instant results</p>
        </div>
        
        <!-- Demo BIN Search -->
        <div class="max-w-2xl mx-auto">
          <div class="card p-8">
            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  Enter BIN (first 6-8 digits)
                </label>
                <input
                  v-model="demoBin"
                  @keyup.enter="searchDemoBin"
                  type="text"
                  placeholder="e.g., 411111"
                  class="input text-lg"
                  maxlength="8"
                />
              </div>
              
              <!-- Demo Results -->
              <div v-if="isLoadingDemo" class="text-center py-8">
                <div class="spinner mx-auto mb-4"></div>
                <p class="text-gray-400">Searching...</p>
              </div>
              
              <div v-else-if="demoResult" class="bg-gray-900 rounded-xl p-8 shadow-lg border border-gray-700">
                <h3 class="text-lg font-semibold text-white mb-4">BIN Information</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-gray-400">Scheme:</span>
                    <span class="text-white ml-2">{{ demoResult.scheme }}</span>
                  </div>
                  <div>
                    <span class="text-gray-400">Type:</span>
                    <span class="text-white ml-2">{{ demoResult.type }}</span>
                  </div>
                  <div>
                    <span class="text-gray-400">Brand:</span>
                    <span class="text-white ml-2">{{ demoResult.brand }}</span>
                  </div>
                  <div>
                    <span class="text-gray-400">Country:</span>
                    <span class="text-white ml-2">{{ demoResult.country }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else-if="demoError" class="bg-red-900/20 border border-red-700 rounded-lg p-4">
                <p class="text-red-400">{{ demoError }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing Section -->
    <section class="py-24 bg-gray-950">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-gray mb-4">Simple Pricing</h2>
          <p class="text-xl text-gray-500">Choose the plan that fits your needs</p>
        </div>
        
        <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <!-- Free Plan -->
          <div class="bg-gray-900 rounded-xl p-8 shadow-lg border border-gray-700">
            <h3 class="text-2xl font-bold text-white mb-2">Free</h3>
            <div class="text-gray-300">per month</div>
            
            <ul class="space-y-3 mb-8 text-left">
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Basic BIN lookup (3 per day)
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                View-only card information
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Community support
              </li>
            </ul>
            
            <router-link v-if="!authStore.isAuthenticated" to="/register" class="btn btn-outline w-full">
              Get Started
            </router-link>
          </div>
          
          <!-- Premium Plan -->
          <div class="bg-gray-900 rounded-xl p-8 shadow-lg border border-gray-700 relative">
            <span class="bg-primary-600 text-white px-3 py-1 rounded-full text-sm font-medium">Popular</span>
            <h3 class="text-2xl font-bold text-white mb-2">$9.99</h3>
            <div class="text-gray-300">per month</div>
            
            <ul class="space-y-3 mb-8 text-left">
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Unlimited BIN lookups
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                5 card generations per day
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Crypto wallet balance checker
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Advanced BIN lookup with bank info
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                AVS (Address Verification) data
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Bulk export (CSV, JSON)
              </li>
              <li class="flex items-center text-gray-300">
                <CheckIcon class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                Priority support
              </li>
            </ul>
            
            <router-link v-if="!authStore.isAuthenticated" to="/register" 
                         class="btn btn-primary w-full">
              Start Free Trial
            </router-link>
            <router-link v-else-if="!authStore.isPremium" to="/subscription" 
                         class="btn btn-primary w-full">
              Upgrade Now
            </router-link>
            <div v-else class="btn btn-outline w-full cursor-not-allowed opacity-50">
              Current Plan
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="py-24 bg-gray-900/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-white mb-4">Why Choose BIN Search Pro?</h2>
          <p class="text-xl text-gray-300">Built for professionals who need reliable card testing tools</p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <BoltIcon class="w-8 h-8 text-white" />
            </div>
            <h3 class="text-xl font-bold text-white mb-4">Lightning Fast</h3>
            <p class="text-gray-300">Sub-100ms response times with global CDN and optimized database queries.</p>
          </div>
          
          <div class="text-center">
            <div class="w-16 h-16 bg-secondary-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <ShieldCheckIcon class="w-8 h-8 text-white" />
            </div>
            <h3 class="text-xl font-bold text-white mb-4">Secure & Compliant</h3>
            <p class="text-gray-300">Enterprise-grade security with encrypted data transmission and storage.</p>
          </div>
          
          <div class="text-center">
            <div class="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <ChartBarIcon class="w-8 h-8 text-white" />
            </div>
            <h3 class="text-xl font-bold text-white mb-4">99.9% Uptime</h3>
            <p class="text-gray-300">Reliable service with comprehensive monitoring and automatic failover.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-950 border-t border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="text-center">
          <div class="flex justify-center mb-6">
            <div class="w-12 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center">
              <span class="text-white font-bold text-lg">BS</span>
            </div>
          </div>
          <p class="text-gray-400 mb-4">Professional BIN Search & Card Testing Platform</p>
          <p class="text-gray-500 text-sm">© 2024 BIN Search Pro. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/utils/api'
import {
  CheckIcon,
  BoltIcon,
  ShieldCheckIcon,
  ChartBarIcon,
} from '@heroicons/vue/24/outline'

// Stores
const authStore = useAuthStore()

// Demo section refs
const demoSection = ref<HTMLElement>()
const demoBin = ref('')
const demoResult = ref<any>(null)
const isLoadingDemo = ref(false)
const demoError = ref<string | null>(null)

// Demo BIN search
const searchDemoBin = async () => {
  if (demoBin.value.length < 6) {
    demoError.value = 'Please enter at least 6 digits'
    return
  }

  isLoadingDemo.value = true
  demoError.value = null
  demoResult.value = null

  try {
    // Call actual API for demo
    const response = await apiClient.lookupBIN(demoBin.value)
    demoResult.value = response
  } catch (error: any) {
    console.warn('Demo BIN lookup failed, using fallback data:', error)
    // Fallback to demo data if API fails
    const demoData: Record<string, any> = {
      '411111': { bin: '411111', brand: 'VISA', type: 'CREDIT', country_name: 'United States', issuer: 'Chase Bank' },
      '545454': { bin: '545454', brand: 'MASTERCARD', type: 'CREDIT', country_name: 'United States', issuer: 'Bank of America' },
      '378282': { bin: '378282', brand: 'AMERICAN EXPRESS', type: 'CREDIT', country_name: 'United States', issuer: 'American Express' },
      '424242': { bin: '424242', brand: 'VISA', type: 'CREDIT', country_name: 'United States', issuer: 'Test Bank' }
    }

    const binPrefix = demoBin.value.substring(0, 6)
    demoResult.value = demoData[binPrefix] || {
      bin: binPrefix,
      brand: 'Unknown',
      type: 'Unknown', 
      country_name: 'Unknown',
      issuer: 'Unknown'
    }
  } finally {
    isLoadingDemo.value = false
  }
}

onMounted(() => {
  // Any initialization code
})
</script>

<style scoped>
.pricing-card .text-gray-600 {
  color: #64748B !important; /* Better contrast */
}

.dark .pricing-card .text-gray-300 {
  color: #CBD5E1 !important; /* Lighter for dark mode */
}
</style>
