import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/styles/main.css'

// Import views
import LandingPage from './views/LandingPage.vue'
import LoginPage from './views/LoginPage.vue'
import RegisterPage from './views/RegisterPage.vue'
import DashboardPage from './views/DashboardPage.vue'
import BinLookupPage from './views/BinLookupPage.vue'
import CardGeneratorPage from './views/CardGeneratorPage.vue'
import CryptoCheckerPage from './views/CryptoCheckerPage.vue'
import SubscriptionPage from './views/SubscriptionPage.vue'
import AdminDashboard from './views/AdminDashboard.vue'

// Auth store for route guards
import { useAuthStore } from './stores/auth'

// Router configuration
const routes = [
  {
    path: '/',
    name: 'home',
    component: LandingPage,
    meta: { requiresAuth: false, title: 'BIN Search Pro' }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { requiresAuth: false, title: 'Login' }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterPage,
    meta: { requiresAuth: false, title: 'Register' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardPage,
    meta: { requiresAuth: true, title: 'Dashboard' }
  },
  {
    path: '/lookup',
    name: 'lookup',
    component: BinLookupPage,
    meta: { requiresAuth: true, title: 'BIN Lookup' }
  },
  {
    path: '/generator',
    name: 'generator',
    component: CardGeneratorPage,
    meta: { requiresAuth: true, title: 'Card Generator' }
  },
  {
    path: '/crypto-checker',
    name: 'crypto-checker',
    component: CryptoCheckerPage,
    meta: { requiresAuth: true, title: 'Crypto Wallet Checker' }
  },
  {
    path: '/subscription',
    name: 'subscription',
    component: SubscriptionPage,
    meta: { requiresAuth: true, title: 'Subscription' }
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Admin Dashboard' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// Global navigation guards
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // Set page title
  document.title = to.meta.title ? `${to.meta.title} - BIN Search Pro` : 'BIN Search Pro'
  
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      next({ name: 'login', query: { redirect: to.fullPath } })
      return
    }
    
    // Check if route requires admin privileges
    if (to.meta.requiresAdmin) {
      if (!authStore.user?.username?.startsWith('admin_')) {
        next({ name: 'dashboard' })
        return
      }
    }
  }
  
  // Redirect authenticated users away from auth pages
  if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }
  
  next()
})

// Create Vue app
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize auth state
const authStore = useAuthStore()
authStore.initAuth()

app.mount('#app')
