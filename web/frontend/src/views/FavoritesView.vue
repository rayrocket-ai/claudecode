<template>
  <div class="max-w-6xl mx-auto p-6 overflow-y-auto h-full">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Saved Properties</h1>

    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="rounded-lg border border-gray-200 overflow-hidden">
        <div class="skeleton h-40"></div>
        <div class="p-3 space-y-2">
          <div class="skeleton h-5 w-24"></div>
          <div class="skeleton h-4 w-40"></div>
        </div>
      </div>
    </div>

    <div v-else-if="favorites.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <PropertyCard
        v-for="fav in favorites"
        :key="fav.id"
        :property="fav.property"
      />
    </div>

    <div v-else class="text-center py-20">
      <p class="text-gray-400 mb-2">No saved properties yet</p>
      <router-link to="/" class="text-sm text-primary-600 hover:text-primary-700">Browse listings</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchFavorites } from '@/api/user'
import PropertyCard from '@/components/property/PropertyCard.vue'

const favorites = ref<unknown[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await fetchFavorites()
    favorites.value = data.data || []
  } finally {
    loading.value = false
  }
})
</script>
