<template>
  <div class="relative" ref="searchRef">
    <div class="relative">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="query"
        @input="onSearch"
        @focus="showResults = true"
        type="text"
        placeholder="Search by address, neighborhood, city, or MLS#"
        class="w-full pl-10 pr-4 py-2 bg-gray-100 border border-transparent rounded-lg text-sm focus:bg-white focus:border-primary-300 focus:ring-1 focus:ring-primary-300 outline-none transition-colors"
      />
    </div>

    <!-- Autocomplete dropdown -->
    <div
      v-if="showResults && results.length > 0"
      class="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden z-50"
    >
      <button
        v-for="result in results"
        :key="`${result.type}-${result.value}`"
        @click="selectResult(result)"
        class="w-full text-left px-4 py-2.5 hover:bg-gray-50 flex items-center gap-3 border-b border-gray-50 last:border-0"
      >
        <span class="text-xs font-medium uppercase text-gray-400 w-20 shrink-0">
          {{ result.type }}
        </span>
        <span class="text-sm text-gray-900">{{ result.label }}</span>
        <span v-if="result.count" class="ml-auto text-xs text-gray-400">
          {{ result.count }} listings
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { onClickOutside, useDebounceFn } from '@vueuse/core'
import { autocomplete } from '@/api/listings'
import { useMapStore } from '@/store/map'
import type { AutocompleteResult } from '@/types'

const router = useRouter()
const mapStore = useMapStore()
const query = ref('')
const results = ref<AutocompleteResult[]>([])
const showResults = ref(false)
const searchRef = ref<HTMLElement>()

onClickOutside(searchRef, () => { showResults.value = false })

const onSearch = useDebounceFn(async () => {
  if (query.value.length < 2) {
    results.value = []
    return
  }
  try {
    results.value = await autocomplete(query.value)
    showResults.value = true
  } catch {
    results.value = []
  }
}, 300)

function selectResult(result: AutocompleteResult) {
  showResults.value = false
  query.value = result.label

  if (result.type === 'address' && result.id) {
    router.push({ name: 'property', params: { id: result.id } })
  } else if (result.type === 'city') {
    mapStore.updateFilters({ city: result.value })
  } else if (result.type === 'neighborhood') {
    mapStore.updateFilters({ neighborhood: result.value, city: result.city })
  }
}
</script>
