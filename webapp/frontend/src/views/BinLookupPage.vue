<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">BIN Lookup</h1>
      <p class="text-gray-400">Search our database of 450,000+ BIN records</p>
    </div>

    <!-- Main Search Component -->
    <BinSearch />
  </div>
</template>

<script setup lang="ts">
import BinSearch from '@/components/BinSearch.vue'
</script>
