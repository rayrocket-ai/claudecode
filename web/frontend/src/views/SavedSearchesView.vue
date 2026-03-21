<template>
  <div class="max-w-4xl mx-auto p-6 overflow-y-auto h-full">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Saved Searches</h1>

    <div v-if="searches.length" class="space-y-3">
      <div
        v-for="search in searches"
        :key="search.id"
        class="border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:shadow-sm transition-shadow"
      >
        <div>
          <h3 class="font-medium text-gray-900">{{ search.name }}</h3>
          <p class="text-sm text-gray-500 mt-0.5">
            {{ formatFilters(search.filters) }}
          </p>
          <p class="text-xs text-gray-400 mt-1">
            {{ search.email_alerts ? `Alerts: ${search.alert_frequency}` : 'Alerts off' }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            @click="applySearch(search)"
            class="px-3 py-1.5 text-sm text-primary-600 border border-primary-200 rounded-lg hover:bg-primary-50"
          >Search</button>
          <button
            @click="handleDelete(search.id)"
            class="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
          >Delete</button>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-20">
      <p class="text-gray-400 mb-2">No saved searches yet</p>
      <router-link to="/" class="text-sm text-primary-600 hover:text-primary-700">Start searching</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSavedSearches, deleteSavedSearch } from '@/api/user'
import { useMapStore } from '@/store/map'
import { formatPrice } from '@/utils/formatters'
import type { SavedSearch, MapFilters } from '@/types'

const router = useRouter()
const mapStore = useMapStore()
const searches = ref<SavedSearch[]>([])

onMounted(async () => {
  searches.value = await fetchSavedSearches()
})

function formatFilters(filters: MapFilters): string {
  const parts = []
  if (filters.status) parts.push(filters.status === 'sold' ? 'Sold' : 'For Sale')
  if (filters.property_type) parts.push(filters.property_type)
  if (filters.price_min || filters.price_max) {
    if (filters.price_min && filters.price_max) parts.push(`${formatPrice(filters.price_min)} - ${formatPrice(filters.price_max)}`)
    else if (filters.price_min) parts.push(`${formatPrice(filters.price_min)}+`)
    else if (filters.price_max) parts.push(`Up to ${formatPrice(filters.price_max)}`)
  }
  if (filters.beds_min) parts.push(`${filters.beds_min}+ beds`)
  return parts.join(' · ') || 'All listings'
}

function applySearch(search: SavedSearch) {
  mapStore.updateFilters(search.filters)
  router.push({ name: 'map', params: { city: 'toronto' } })
}

async function handleDelete(id: number) {
  await deleteSavedSearch(id)
  searches.value = searches.value.filter(s => s.id !== id)
}
</script>
