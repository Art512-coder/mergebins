import { ref } from 'vue'
import { apiClient } from '@/utils/api'
import { downloadFile, generateCSV } from '@/utils/helpers'
import type { GeneratedCard, CardGenerationRequest } from '@/types'

export function useCardGenerator() {
  const cards = ref<GeneratedCard[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const rateLimitStatus = ref<any>(null)
  const generationParams = ref<CardGenerationRequest>({
    count: 1,
    format: 'json',
    include_avs: false,
  })

  const loadRateLimitStatus = async () => {
    try {
      const status = await apiClient.getCardGenerationStatus()
      rateLimitStatus.value = status
    } catch (err: any) {
      console.warn('Failed to load rate limit status:', err.message)
    }
  }

  const generateCards = async (params?: Partial<CardGenerationRequest>) => {
    const request = { ...generationParams.value, ...params }
    
    if (request.count < 1 || request.count > 100) {
      error.value = 'Card count must be between 1 and 100'
      return
    }

    // Check rate limits before attempting generation
    await loadRateLimitStatus()
    if (rateLimitStatus.value?.remaining <= 0) {
      error.value = `Daily limit reached. You can generate ${rateLimitStatus.value.daily_limit} cards every 24 hours. Reset time: ${new Date(rateLimitStatus.value.reset_time).toLocaleString()}`
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.generateCards(request) as { cards: any[] }
      cards.value = response.cards || []
      
      // Refresh rate limit status after successful generation
      await loadRateLimitStatus()
    } catch (err: any) {
      error.value = err.message || 'Failed to generate cards'
      cards.value = []
    } finally {
      isLoading.value = false
    }
  }

  const exportCards = async (format: 'json' | 'csv' | 'txt') => {
    if (cards.value.length === 0) {
      error.value = 'No cards to export'
      return
    }

    try {
      let content: string
      let filename: string
      let contentType: string

      switch (format) {
        case 'json':
          content = JSON.stringify(cards.value, null, 2)
          filename = `cards-${Date.now()}.json`
          contentType = 'application/json'
          break

        case 'csv':
          const headers = ['number', 'cvv', 'expiry', 'brand', 'type', 'country']
          content = generateCSV(cards.value, headers)
          filename = `cards-${Date.now()}.csv`
          contentType = 'text/csv'
          break

        case 'txt':
          content = cards.value
            .map(card => `${card.number} | ${card.cvv} | ${card.expiry} | ${card.brand}`)
            .join('\n')
          filename = `cards-${Date.now()}.txt`
          contentType = 'text/plain'
          break

        default:
          throw new Error('Unsupported export format')
      }

      downloadFile(content, filename, contentType)
    } catch (err: any) {
      error.value = err.message || 'Failed to export cards'
    }
  }

  const clearCards = () => {
    cards.value = []
    error.value = null
  }

  const copyCard = (card: GeneratedCard) => {
    const cardText = `${card.number} | ${card.cvv} | ${card.expiry}`
    navigator.clipboard.writeText(cardText)
  }

  const copyAllCards = () => {
    const allCardsText = cards.value
      .map(card => `${card.number} | ${card.cvv} | ${card.expiry}`)
      .join('\n')
    navigator.clipboard.writeText(allCardsText)
  }

  return {
    cards,
    isLoading,
    error,
    rateLimitStatus,
    generationParams,
    generateCards,
    exportCards,
    clearCards,
    copyCard,
    copyAllCards,
    loadRateLimitStatus,
  }
}
