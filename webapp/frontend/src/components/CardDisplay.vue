<template>
  <div 
    :class="[
      'credit-card relative overflow-hidden rounded-xl p-6 text-white shadow-2xl transition-all duration-300 hover:scale-105 cursor-pointer',
      cardClass
    ]"
    @click="copyCard"
  >
    <!-- Background pattern -->
    <div class="absolute inset-0 opacity-10">
      <div class="absolute top-4 left-4 w-8 h-8 bg-white/20 rounded-full"></div>
      <div class="absolute top-8 right-8 w-4 h-4 bg-white/10 rounded-full"></div>
      <div class="absolute bottom-6 left-8 w-6 h-6 bg-white/15 rounded-full"></div>
    </div>
    
    <!-- Card content -->
    <div class="relative z-10">
      <!-- Card brand and type -->
      <div class="flex justify-between items-start mb-6">
        <div class="text-xs uppercase tracking-wide opacity-80">
          {{ card.type }}
        </div>
        <div class="text-lg font-bold">
          {{ card.brand }}
        </div>
      </div>
      
      <!-- Card number -->
      <div class="mb-6">
        <div class="text-xl lg:text-2xl font-mono tracking-wider">
          {{ formattedNumber }}
        </div>
      </div>
      
      <!-- Card details -->
      <div class="flex justify-between items-end">
        <div>
          <div class="text-xs opacity-70 mb-1">EXPIRES</div>
          <div class="text-sm font-medium">{{ card.expiry }}</div>
        </div>
        <div>
          <div class="text-xs opacity-70 mb-1">CVV</div>
          <div class="text-sm font-medium">{{ card.cvv }}</div>
        </div>
        <div v-if="card.country">
          <div class="text-xs opacity-70 mb-1">COUNTRY</div>
          <div class="text-sm font-medium">{{ card.country }}</div>
        </div>
      </div>
    </div>
    
    <!-- Hover overlay -->
    <div class="absolute inset-0 bg-white/5 opacity-0 hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
      <div class="text-center">
        <DocumentDuplicateIcon class="w-8 h-8 mx-auto mb-2" />
        <div class="text-sm font-medium">Click to copy</div>
      </div>
    </div>
    
    <!-- Copy success indicator -->
    <transition name="scale">
      <div v-if="showCopySuccess" class="absolute inset-0 bg-green-500/20 flex items-center justify-center">
        <div class="text-center">
          <CheckIcon class="w-8 h-8 mx-auto mb-2 text-green-400" />
          <div class="text-sm font-medium text-green-400">Copied!</div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { formatCardNumber, copyToClipboard } from '@/utils/helpers'
import type { GeneratedCard } from '@/types'
import { DocumentDuplicateIcon, CheckIcon } from '@heroicons/vue/24/outline'

interface Props {
  card: GeneratedCard
}

const props = defineProps<Props>()

const showCopySuccess = ref(false)

// Computed
const formattedNumber = computed(() => {
  return formatCardNumber(props.card.number)
})

const cardClass = computed(() => {
  const brand = props.card.brand.toLowerCase()
  switch (brand) {
    case 'visa':
      return 'visa'
    case 'mastercard':
      return 'mastercard'
    case 'amex':
    case 'american express':
      return 'amex'
    default:
      return ''
  }
})

// Methods
const copyCard = async () => {
  const cardText = `${props.card.number} | ${props.card.cvv} | ${props.card.expiry}`
  
  const success = await copyToClipboard(cardText)
  if (success) {
    showCopySuccess.value = true
    setTimeout(() => {
      showCopySuccess.value = false
    }, 1500)
    
    window.addToast?.({
      type: 'success',
      title: 'Card copied!',
      message: 'Card details copied to clipboard.',
    })
  }
}
</script>

<style scoped>
.scale-enter-active, .scale-leave-active {
  transition: all 0.3s ease;
}

.scale-enter-from, .scale-leave-to {
  transform: scale(0.8);
  opacity: 0;
}
</style>
