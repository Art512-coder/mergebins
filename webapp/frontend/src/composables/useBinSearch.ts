import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import type { BINResult, BINSearchHistory } from '@/types'

// Simple in-memory cache for recent searches
const searchCache = new Map<string, { result: BINResult; timestamp: number }>()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes
const MAX_CACHE_SIZE = 100

export function useBinSearch() {
  const query = ref('')
  const result = ref<BINResult | null>(null)
  const history = ref<BINSearchHistory[]>([])
  const favorites = ref<string[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const retryCount = ref(0)

  const isValidBIN = computed(() => {
    return /^\d{6,8}$/.test(query.value)
  })

  const searchBIN = async (bin?: string, skipCache = false) => {
    const searchTerm = bin || query.value
    
    if (!searchTerm || searchTerm.length < 6) {
      error.value = 'Please enter at least 6 digits'
      return
    }

    // Check cache first (unless explicitly skipping)
    if (!skipCache) {
      const cached = getCachedResult(searchTerm)
      if (cached) {
        result.value = cached
        return
      }
    }

    isLoading.value = true
    error.value = null
    retryCount.value = 0

    try {
      const response = await performSearch(searchTerm)
      result.value = response as BINResult
      
      // Cache the result
      setCacheResult(searchTerm, response as BINResult)
      
      // Add to history
      addToSearchHistory(searchTerm, response as BINResult)
      
      // Save history to localStorage
      saveHistoryToStorage()
      
    } catch (err: any) {
      await handleSearchError(err, searchTerm)
    } finally {
      isLoading.value = false
    }
  }

  const performSearch = async (bin: string): Promise<BINResult> => {
    try {
      const response = await apiClient.lookupBIN(bin)
      return response as BINResult
    } catch (err: any) {
      // Retry logic for network failures
      if (retryCount.value < 2 && isRetryableError(err)) {
        retryCount.value++
        await delay(1000 * retryCount.value) // Progressive delay
        return performSearch(bin)
      }
      throw err
    }
  }

  const handleSearchError = async (err: any, bin: string) => {
    if (err.status === 429) {
      error.value = 'Rate limit exceeded. Please wait a moment and try again.'
    } else if (err.status === 404) {
      error.value = `No information found for BIN ${bin}`
    } else if (!navigator.onLine) {
      error.value = 'No internet connection. Please check your network.'
    } else if (retryCount.value > 0) {
      error.value = `Failed to lookup BIN after ${retryCount.value + 1} attempts`
    } else {
      error.value = err.message || 'Failed to lookup BIN'
    }
    result.value = null
  }

  const isRetryableError = (err: any) => {
    return err.status >= 500 || err.code === 'NETWORK_ERROR' || !navigator.onLine
  }

  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  const getCachedResult = (bin: string): BINResult | null => {
    const cached = searchCache.get(bin)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.result
    }
    // Remove expired cache
    if (cached) {
      searchCache.delete(bin)
    }
    return null
  }

  const setCacheResult = (bin: string, result: BINResult) => {
    // Manage cache size
    if (searchCache.size >= MAX_CACHE_SIZE) {
      const oldestKey = searchCache.keys().next().value
      if (oldestKey) {
        searchCache.delete(oldestKey)
      }
    }
    
    searchCache.set(bin, {
      result,
      timestamp: Date.now()
    })
  }

  const addToSearchHistory = (bin: string, searchResult: BINResult) => {
    const historyItem: BINSearchHistory = {
      id: Date.now().toString(),
      bin,
      result: searchResult,
      searched_at: new Date().toISOString(),
      user_id: 'current-user', // This would come from auth store
    }
    
    // Remove duplicate if exists
    history.value = history.value.filter(item => item.bin !== bin)
    history.value.unshift(historyItem)
    
    // Keep only last 20 searches
    if (history.value.length > 20) {
      history.value = history.value.slice(0, 20)
    }
  }

  const saveHistoryToStorage = () => {
    try {
      localStorage.setItem('bin_search_history', JSON.stringify(history.value))
    } catch (err) {
      console.warn('Failed to save search history to localStorage:', err)
    }
  }

  const loadHistoryFromStorage = () => {
    try {
      const saved = localStorage.getItem('bin_search_history')
      if (saved) {
        const parsed = JSON.parse(saved)
        // Validate and filter recent history (last 7 days)
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000
        history.value = parsed.filter((item: BINSearchHistory) => 
          new Date(item.searched_at).getTime() > weekAgo
        )
      }
    } catch (err) {
      console.warn('Failed to load search history from localStorage:', err)
      history.value = []
    }
  }

  const addToFavorites = (bin: string) => {
    if (!favorites.value.includes(bin)) {
      favorites.value.push(bin)
      // Save to localStorage
      localStorage.setItem('bin_favorites', JSON.stringify(favorites.value))
    }
  }

  const removeFromFavorites = (bin: string) => {
    favorites.value = favorites.value.filter(fav => fav !== bin)
    localStorage.setItem('bin_favorites', JSON.stringify(favorites.value))
  }

  const isFavorite = (bin: string) => {
    return favorites.value.includes(bin)
  }

  const loadFavorites = () => {
    const saved = localStorage.getItem('bin_favorites')
    if (saved) {
      favorites.value = JSON.parse(saved)
    }
  }

  const clearHistory = () => {
    history.value = []
  }

  // Load favorites and history on initialization
  loadFavorites()
  loadHistoryFromStorage()

  return {
    query,
    result,
    history,
    favorites,
    isLoading,
    error,
    isValidBIN,
    searchBIN,
    addToFavorites,
    removeFromFavorites,
    isFavorite,
    clearHistory,
  }
}
