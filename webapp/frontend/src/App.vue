<template>
  <div id="app" class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Navigation -->
    <nav v-if="authStore.isAuthenticated" class="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo -->
          <router-link to="/dashboard" class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold text-sm">BS</span>
            </div>
            <span class="text-xl font-bold text-gradient">BIN Search Pro</span>
          </router-link>

          <!-- Navigation Links -->
          <div class="hidden md:flex items-center space-x-6">
            <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
            <router-link to="/lookup" class="nav-link">BIN Lookup</router-link>
            <router-link to="/generator" class="nav-link">Card Generator</router-link>
            <router-link to="/crypto-checker" class="nav-link">Crypto Checker</router-link>
            <router-link to="/subscription" class="nav-link">Subscription</router-link>
          </div>

          <!-- User Menu -->
          <div class="flex items-center space-x-4">
            <!-- Theme Toggle -->
            <button @click="themeStore.toggleTheme()" class="p-2 rounded-lg hover:bg-gray-800 transition-colors">
              <SunIcon v-if="themeStore.isDark" class="w-5 h-5" />
              <MoonIcon v-else class="w-5 h-5" />
            </button>

            <!-- User Dropdown -->
            <div class="relative">
              <button @click="showUserMenu = !showUserMenu" class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-800 transition-colors">
                <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                  <span class="text-sm font-medium text-white">{{ userInitials }}</span>
                </div>
                <ChevronDownIcon class="w-4 h-4" />
              </button>
              
              <!-- Dropdown Menu -->
              <div v-show="showUserMenu" class="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-1 z-50">
                <div class="px-4 py-2 border-b border-gray-700">
                  <p class="text-sm font-medium">{{ authStore.user?.username }}</p>
                  <p class="text-xs text-gray-400">{{ authStore.user?.plan }} plan</p>
                </div>
                <button @click="logout" class="w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors">
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1">
      <router-view />
    </main>

    <!-- Toast Notifications -->
    <div class="fixed bottom-4 right-4 z-50 space-y-2">
      <div v-for="toast in toasts" :key="toast.id" 
           class="bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-lg max-w-sm slide-up">
        <div class="flex items-start space-x-3">
          <CheckCircleIcon v-if="toast.type === 'success'" class="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
          <ExclamationTriangleIcon v-else-if="toast.type === 'error'" class="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <InformationCircleIcon v-else class="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div class="flex-1">
            <p class="text-sm font-medium">{{ toast.title }}</p>
            <p v-if="toast.message" class="text-xs text-gray-400 mt-1">{{ toast.message }}</p>
          </div>
          <button @click="removeToast(toast.id)" class="text-gray-400 hover:text-white">
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePaymentStore } from '@/stores/payment'
import { useTheme } from '@/composables/useTheme'
import {
  SunIcon,
  MoonIcon,
  ChevronDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

// Stores
const authStore = useAuthStore()
const paymentStore = usePaymentStore()
const themeStore = useTheme()
const router = useRouter()

// Local state
const showUserMenu = ref(false)

// Toast system
interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  title: string
  message?: string
}

const toasts = ref<Toast[]>([])

const addToast = (toast: Omit<Toast, 'id'>) => {
  const id = Date.now().toString()
  toasts.value.push({ ...toast, id })
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    removeToast(id)
  }, 5000)
}

const removeToast = (id: string) => {
  toasts.value = toasts.value.filter(toast => toast.id !== id)
}

// Computed
const userInitials = computed(() => {
  const user = authStore.user
  if (!user) return 'U'
  return user.username.substring(0, 2).toUpperCase()
})

// Methods
const logout = () => {
  authStore.logout()
  router.push('/')
  addToast({
    type: 'info',
    title: 'Signed out',
    message: 'You have been successfully signed out.'
  })
}

// Global click handler to close menus
const handleGlobalClick = (event: Event) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    showUserMenu.value = false
  }
}

// Lifecycle
onMounted(() => {
  // Initialize theme
  themeStore.initTheme()
  
  // Load user data if authenticated
  if (authStore.isAuthenticated) {
    paymentStore.loadUsageStats()
    paymentStore.loadSubscription()
  }
  
  // Add global click listener
  document.addEventListener('click', handleGlobalClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
})

// Expose toast system globally (safely)
if (!window.addToast) {
  window.addToast = addToast
}

// Add missing global functions to prevent ReferenceError
if (!window.openLogin) {
  window.openLogin = () => {
    router.push('/login')
  }
}

if (!window.openCryptoChecker) {
  window.openCryptoChecker = () => {
    router.push('/crypto-checker')
  }
}

// Prevent currentUser variable redeclaration issues
if (!window.currentUser) {
  window.currentUser = null
}
</script>

<style scoped>
.nav-link {
  @apply text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors;
}

.nav-link.router-link-active {
  @apply text-white bg-gray-800;
}
</style>
