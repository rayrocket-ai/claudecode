<template>
  <div class="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-3 overflow-x-auto shrink-0">
    <!-- Status toggle -->
    <div class="flex rounded-lg border border-gray-300 overflow-hidden shrink-0">
      <button
        @click="updateFilter('status', 'for-sale')"
        :class="['px-3 py-1.5 text-xs font-medium transition-colors', filters.status === 'for-sale' ? 'bg-primary-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50']"
      >For Sale</button>
      <button
        @click="updateFilter('status', 'sold')"
        :class="['px-3 py-1.5 text-xs font-medium transition-colors border-l border-gray-300', filters.status === 'sold' ? 'bg-red-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50']"
      >Sold</button>
    </div>

    <!-- Price -->
    <div class="relative shrink-0" ref="priceRef">
      <button @click="showPrice = !showPrice" :class="['filter-chip', (filters.price_min || filters.price_max) ? 'active' : '']">
        {{ priceLabel }}
        <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
      </button>
      <div v-if="showPrice" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-40 w-64">
        <p class="text-xs font-medium text-gray-500 mb-2">Price Range</p>
        <div class="flex gap-2 items-center">
          <input v-model.number="localPriceMin" type="number" placeholder="Min" step="50000" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
          <span class="text-gray-400">-</span>
          <input v-model.number="localPriceMax" type="number" placeholder="Max" step="50000" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <div class="flex gap-2 mt-3">
          <button @click="clearPrice" class="flex-1 text-xs text-gray-600 border border-gray-300 rounded py-1.5 hover:bg-gray-50">Clear</button>
          <button @click="applyPrice" class="flex-1 text-xs text-white bg-primary-600 rounded py-1.5 hover:bg-primary-700">Apply</button>
        </div>
      </div>
    </div>

    <!-- Beds -->
    <div class="flex items-center gap-1 shrink-0">
      <span class="text-xs text-gray-500 mr-1">Beds</span>
      <button
        v-for="n in [0, 1, 2, 3, 4, 5]"
        :key="n"
        @click="updateFilter('beds_min', filters.beds_min === n ? undefined : n)"
        :class="['w-7 h-7 rounded-full text-xs font-medium transition-colors', filters.beds_min === n ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']"
      >{{ n === 0 ? 'Any' : n + '+' }}</button>
    </div>

    <!-- Property Type -->
    <div class="relative shrink-0" ref="typeRef">
      <button @click="showType = !showType" :class="['filter-chip', filters.property_type ? 'active' : '']">
        {{ filters.property_type ? formatPropertyType(filters.property_type) : 'Type' }}
        <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
      </button>
      <div v-if="showType" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-40 w-48">
        <button
          v-for="type in propertyTypes"
          :key="type.value"
          @click="selectType(type.value)"
          :class="['w-full text-left px-4 py-2 text-sm hover:bg-gray-50', filters.property_type === type.value ? 'text-primary-600 font-medium' : 'text-gray-700']"
        >{{ type.label }}</button>
      </div>
    </div>

    <!-- Sold within (only when sold tab active) -->
    <div v-if="filters.status === 'sold'" class="relative shrink-0" ref="soldRef">
      <button @click="showSold = !showSold" :class="['filter-chip', filters.sold_within_days ? 'active' : '']">
        {{ soldLabel }}
        <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
      </button>
      <div v-if="showSold" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-40 w-40">
        <button
          v-for="opt in soldOptions"
          :key="opt.value"
          @click="updateFilter('sold_within_days', opt.value); showSold = false"
          class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >{{ opt.label }}</button>
      </div>
    </div>

    <!-- Results count -->
    <span class="ml-auto text-xs text-gray-500 shrink-0">
      {{ mapStore.totalResults.toLocaleString() }} results
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { useMapStore } from '@/store/map'
import { formatPrice, formatPropertyType } from '@/utils/formatters'

const mapStore = useMapStore()
const filters = mapStore.filters

const showPrice = ref(false)
const showType = ref(false)
const showSold = ref(false)
const localPriceMin = ref<number | undefined>(filters.price_min)
const localPriceMax = ref<number | undefined>(filters.price_max)

const priceRef = ref<HTMLElement>()
const typeRef = ref<HTMLElement>()
const soldRef = ref<HTMLElement>()

onClickOutside(priceRef, () => { showPrice.value = false })
onClickOutside(typeRef, () => { showType.value = false })
onClickOutside(soldRef, () => { showSold.value = false })

const propertyTypes = [
  { value: '', label: 'All Types' },
  { value: 'detached', label: 'Detached' },
  { value: 'semi-detached', label: 'Semi-Detached' },
  { value: 'townhouse', label: 'Townhouse' },
  { value: 'condo-apt', label: 'Condo' },
  { value: 'condo-townhouse', label: 'Condo Townhouse' },
  { value: 'duplex', label: 'Duplex' },
  { value: 'triplex', label: 'Triplex' },
]

const soldOptions = [
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
  { value: 180, label: 'Last 6 months' },
  { value: 365, label: 'Last year' },
]

const priceLabel = computed(() => {
  if (filters.price_min && filters.price_max) return `${formatPrice(filters.price_min)} - ${formatPrice(filters.price_max)}`
  if (filters.price_min) return `${formatPrice(filters.price_min)}+`
  if (filters.price_max) return `Up to ${formatPrice(filters.price_max)}`
  return 'Price'
})

const soldLabel = computed(() => {
  const opt = soldOptions.find(o => o.value === filters.sold_within_days)
  return opt ? opt.label : 'Time Period'
})

function updateFilter(key: string, value: unknown) {
  mapStore.updateFilters({ [key]: value })
}

function selectType(value: string) {
  updateFilter('property_type', value || undefined)
  showType.value = false
}

function applyPrice() {
  mapStore.updateFilters({ price_min: localPriceMin.value, price_max: localPriceMax.value })
  showPrice.value = false
}

function clearPrice() {
  localPriceMin.value = undefined
  localPriceMax.value = undefined
  mapStore.updateFilters({ price_min: undefined, price_max: undefined })
  showPrice.value = false
}
</script>
