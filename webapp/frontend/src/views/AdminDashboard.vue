<!-- Admin Dashboard Vue Component -->
<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
    <nav class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-bold text-gray-900">🛡️ Admin Dashboard</h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">{{ user?.username }}</span>
            <button @click="logout" class="text-sm text-red-600 hover:text-red-800">
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <!-- Stats Overview -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <i class="fas fa-users text-white text-sm"></i>
              </div>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-500">Total Users</p>
              <p class="text-2xl font-bold text-gray-900">{{ stats?.total_users || 0 }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <i class="fas fa-dollar-sign text-white text-sm"></i>
              </div>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-500">Revenue</p>
              <p class="text-2xl font-bold text-gray-900">${{ stats?.total_revenue || 0 }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                <i class="fas fa-search text-white text-sm"></i>
              </div>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-500">Total Searches</p>
              <p class="text-2xl font-bold text-gray-900">{{ stats?.total_searches || 0 }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                <i class="fas fa-crown text-white text-sm"></i>
              </div>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-500">Premium Users</p>
              <p class="text-2xl font-bold text-gray-900">{{ stats?.premium_users || 0 }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white shadow rounded-lg">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8 px-6">
            <button 
              v-for="tab in tabs" 
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                activeTab === tab.id 
                  ? 'border-indigo-500 text-indigo-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
              ]"
            >
              {{ tab.label }}
            </button>
          </nav>
        </div>

        <div class="p-6">
          <!-- Users Tab -->
          <div v-if="activeTab === 'users'" class="space-y-6">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium text-gray-900">User Management</h3>
              <div class="flex space-x-2">
                <input 
                  v-model="searchQuery" 
                  placeholder="Search users..."
                  class="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                <button 
                  @click="loadUsers"
                  class="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
                >
                  Refresh
                </button>
              </div>
            </div>

            <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table class="min-w-full divide-y divide-gray-300">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">User</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Plan</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Searches</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Joined</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Actions</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="user in filteredUsers" :key="user.id">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm font-medium text-gray-900">{{ user.username }}</div>
                      <div class="text-sm text-gray-500">{{ user.email }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span :class="[
                        user.plan === 'pro' ? 'bg-purple-100 text-purple-800' :
                        user.plan === 'premium' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800',
                        'inline-flex px-2 py-1 text-xs font-semibold rounded-full'
                      ]">
                        {{ user.plan }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ user.search_count || 0 }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ new Date(user.created_at).toLocaleDateString() }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button class="text-indigo-600 hover:text-indigo-900 mr-2">View</button>
                      <button class="text-red-600 hover:text-red-900">Block</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Payments Tab -->
          <div v-if="activeTab === 'payments'" class="space-y-6">
            <h3 class="text-lg font-medium text-gray-900">Payment Monitoring</h3>
            
            <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table class="min-w-full divide-y divide-gray-300">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Payment ID</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">User</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Amount</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Date</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="payment in payments" :key="payment.payment_id">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {{ payment.payment_id }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ payment.username }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ payment.amount }} {{ payment.currency }} (${{ payment.amount_usd }})
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span :class="[
                        payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                        payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800',
                        'inline-flex px-2 py-1 text-xs font-semibold rounded-full'
                      ]">
                        {{ payment.status }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ new Date(payment.created_at).toLocaleDateString() }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Analytics Tab -->
          <div v-if="activeTab === 'analytics'" class="space-y-6">
            <h3 class="text-lg font-medium text-gray-900">Platform Analytics</h3>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Top BINs -->
              <div class="bg-white border rounded-lg p-6">
                <h4 class="text-lg font-medium text-gray-900 mb-4">Top Searched BINs</h4>
                <div class="space-y-3">
                  <div v-for="bin in analytics?.top_bins || []" :key="bin.bin_number" 
                       class="flex justify-between items-center">
                    <span class="font-mono text-sm">{{ bin.bin_number }}</span>
                    <span class="text-sm text-gray-500">{{ bin.search_count }} searches</span>
                  </div>
                </div>
              </div>

              <!-- User Activity -->
              <div class="bg-white border rounded-lg p-6">
                <h4 class="text-lg font-medium text-gray-900 mb-4">User Activity by Plan</h4>
                <div class="space-y-3">
                  <div v-for="activity in analytics?.user_activity || []" :key="activity.plan"
                       class="flex justify-between items-center">
                    <span class="capitalize">{{ activity.plan }} Users</span>
                    <div class="text-right">
                      <div class="text-sm font-medium">{{ activity.user_count }} users</div>
                      <div class="text-xs text-gray-500">{{ Math.round(activity.avg_searches || 0) }} avg searches</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('users')
const stats = ref<any>(null)
const users = ref<any[]>([])
const payments = ref<any[]>([])
const analytics = ref<any>(null)
const searchQuery = ref('')
const loading = ref(false)

const tabs = [
  { id: 'users', label: 'Users' },
  { id: 'payments', label: 'Payments' },
  { id: 'analytics', label: 'Analytics' }
]

const user = computed(() => authStore.user)

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(user => 
    user.username.toLowerCase().includes(query) ||
    user.email.toLowerCase().includes(query)
  )
})

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const loadStats = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/stats`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      stats.value = data.platform_stats
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadUsers = async () => {
  try {
    loading.value = true
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/users`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      users.value = data.users
    }
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

const loadPayments = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/payments`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      payments.value = data.payments
    }
  } catch (error) {
    console.error('Failed to load payments:', error)
  }
}

const loadAnalytics = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/analytics`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      analytics.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load analytics:', error)
  }
}

onMounted(async () => {
  // Check if user is admin
  if (!authStore.user?.username?.startsWith('admin_')) {
    router.push('/')
    return
  }

  await Promise.all([
    loadStats(),
    loadUsers(),
    loadPayments(),
    loadAnalytics()
  ])
})
</script>