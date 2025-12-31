<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Header -->
      <div class="text-center">
        <div class="flex justify-center mb-6">
          <div class="w-16 h-16 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl flex items-center justify-center shadow-2xl">
            <span class="text-white font-bold text-2xl">BS</span>
          </div>
        </div>
        <h2 class="text-3xl font-bold text-white">Welcome back</h2>
        <p class="mt-2 text-gray-400">Sign in to your account</p>
      </div>

      <!-- Login Form -->
      <div class="card p-8">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Username -->
          <div>
            <label for="username" class="block text-sm font-medium text-gray-300 mb-2">
              Username
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              required
              class="input"
              placeholder="Enter your username"
              :disabled="isLoading"
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                class="input pr-10"
                placeholder="Enter your password"
                :disabled="isLoading"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                :disabled="isLoading"
              >
                <EyeIcon v-if="!showPassword" class="w-5 h-5 text-gray-400 hover:text-gray-300" />
                <EyeSlashIcon v-else class="w-5 h-5 text-gray-400 hover:text-gray-300" />
              </button>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="bg-red-900/20 border border-red-700 rounded-lg p-3">
            <p class="text-red-400 text-sm">{{ error }}</p>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="isLoading || !isFormValid"
            class="btn btn-primary w-full text-lg py-3"
          >
            <div v-if="isLoading" class="flex items-center justify-center">
              <div class="spinner mr-2"></div>
              Signing in...
            </div>
            <span v-else>Sign in</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="mt-6">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-700"></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-gray-800 text-gray-400">Don't have an account?</span>
            </div>
          </div>
          
          <div class="mt-4">
            <router-link to="/register" class="btn btn-outline w-full">
              Create account
            </router-link>
          </div>
        </div>
      </div>

      <!-- Back to home -->
      <div class="text-center">
        <router-link to="/" class="text-primary-400 hover:text-primary-300 text-sm">
          ← Back to home
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'

// Router
const router = useRouter()
const route = useRoute()

// Store
const authStore = useAuthStore()

// Form state
const form = ref({
  username: '',
  password: '',
})

const showPassword = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)

// Computed
const isFormValid = computed(() => {
  return form.value.username.length > 0 && form.value.password.length > 0
})

// Methods
const handleLogin = async () => {
  if (!isFormValid.value || isLoading.value) return

  isLoading.value = true
  error.value = null

  try {
    const success = await authStore.login({
      username: form.value.username,
      password: form.value.password,
    })

    if (success) {
      // Redirect to intended page or dashboard
      const redirectTo = (route.query.redirect as string) || '/dashboard'
      router.push(redirectTo)
      
      // Show success message
      window.addToast?.({
        type: 'success',
        title: 'Welcome back!',
        message: 'You have been successfully signed in.',
      })
    }
  } catch (err: any) {
    error.value = err.message || 'Login failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}

// Demo credentials hint
// const fillDemoCredentials = () => {
//   form.value.username = 'demo'
//   form.value.password = 'demo123'
// }
</script>
