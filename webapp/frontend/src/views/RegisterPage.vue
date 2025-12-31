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
        <h2 class="text-3xl font-bold text-white">Create Account</h2>
        <p class="mt-2 text-gray-400">Join thousands of developers and QA testers</p>
      </div>

      <!-- Registration Form -->
      <div class="card p-8">
        <form @submit.prevent="handleRegister" class="space-y-6">
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
              placeholder="Choose a username"
              :disabled="isLoading"
            />
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="input"
              placeholder="your@email.com"
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
                placeholder="Create a password"
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
            <!-- Password strength indicator -->
            <div v-if="form.password" class="mt-2">
              <div class="flex space-x-1">
                <div
                  v-for="i in 4"
                  :key="i"
                  :class="[
                    'h-1 rounded-full flex-1',
                    i <= passwordStrength ? getStrengthColor(passwordStrength) : 'bg-gray-700'
                  ]"
                ></div>
              </div>
              <p class="text-xs mt-1" :class="getStrengthTextColor(passwordStrength)">
                {{ getStrengthText(passwordStrength) }}
              </p>
            </div>
          </div>

          <!-- Terms -->
          <div class="flex items-start">
            <input
              id="terms"
              v-model="form.acceptTerms"
              type="checkbox"
              class="w-4 h-4 text-primary-600 bg-gray-800 border-gray-600 rounded focus:ring-primary-500"
              :disabled="isLoading"
            />
            <label for="terms" class="ml-2 text-sm text-gray-300">
              I agree to the 
              <a href="#" class="text-primary-400 hover:text-primary-300">Terms of Service</a>
              and 
              <a href="#" class="text-primary-400 hover:text-primary-300">Privacy Policy</a>
            </label>
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
              Creating account...
            </div>
            <span v-else>Create Account</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="mt-6">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-700"></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-gray-800 text-gray-400">Already have an account?</span>
            </div>
          </div>
          
          <div class="mt-4">
            <router-link to="/login" class="btn btn-outline w-full">
              Sign in instead
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
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { validateEmail, validatePassword } from '@/utils/helpers'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'

// Router
const router = useRouter()

// Store
const authStore = useAuthStore()

// Form state
const form = ref({
  username: '',
  email: '',
  password: '',
  acceptTerms: false,
})

const showPassword = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)

// Computed
const isFormValid = computed(() => {
  return (
    form.value.username.length >= 3 &&
    validateEmail(form.value.email) &&
    form.value.password.length >= 8 &&
    form.value.acceptTerms
  )
})

const passwordStrength = computed(() => {
  const password = form.value.password
  if (!password) return 0
  
  let strength = 0
  if (password.length >= 8) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^A-Za-z0-9]/.test(password)) strength++
  
  return Math.min(strength, 4)
})

// Methods
const getStrengthColor = (strength: number) => {
  switch (strength) {
    case 1: return 'bg-red-500'
    case 2: return 'bg-yellow-500'
    case 3: return 'bg-blue-500'
    case 4: return 'bg-green-500'
    default: return 'bg-gray-700'
  }
}

const getStrengthTextColor = (strength: number) => {
  switch (strength) {
    case 1: return 'text-red-400'
    case 2: return 'text-yellow-400'
    case 3: return 'text-blue-400'
    case 4: return 'text-green-400'
    default: return 'text-gray-500'
  }
}

const getStrengthText = (strength: number) => {
  switch (strength) {
    case 1: return 'Weak password'
    case 2: return 'Fair password'
    case 3: return 'Good password'
    case 4: return 'Strong password'
    default: return 'Enter password'
  }
}

const handleRegister = async () => {
  if (!isFormValid.value || isLoading.value) return

  // Validate email
  if (!validateEmail(form.value.email)) {
    error.value = 'Please enter a valid email address'
    return
  }

  // Validate password
  const passwordValidation = validatePassword(form.value.password)
  if (!passwordValidation.isValid) {
    error.value = passwordValidation.errors[0]
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const success = await authStore.register({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
    })

    if (success) {
      router.push('/dashboard')
      
      // Show success message
      window.addToast?.({
        type: 'success',
        title: 'Welcome to BIN Search Pro!',
        message: 'Your account has been created successfully.',
      })
    }
  } catch (err: any) {
    error.value = err.message || 'Registration failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
