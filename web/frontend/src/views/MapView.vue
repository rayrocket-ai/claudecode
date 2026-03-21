<template>
  <div class="h-full flex flex-col">
    <!-- Filter bar -->
    <FilterPanel />

    <!-- Map + List split -->
    <div class="flex-1 flex overflow-hidden">
      <!-- List panel (collapsible) -->
      <div
        v-if="mapStore.showListPanel"
        class="w-96 border-r border-gray-200 flex flex-col bg-white shrink-0 hidden lg:flex"
      >
        <div class="p-3 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-900">
            {{ mapStore.totalResults.toLocaleString() }} Listings
          </h2>
          <button @click="mapStore.showListPanel = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3">
          <PropertyCard
            v-for="feature in listingCards"
            :key="feature.properties.id"
            :property="featureToProperty(feature)"
            @hover="mapStore.selectProperty($event)"
          />

          <div v-if="mapStore.listings.length === 0 && !mapStore.loading" class="text-center py-12 text-gray-400">
            <p class="text-sm">No listings in this area</p>
            <p class="text-xs mt-1">Try zooming out or adjusting filters</p>
          </div>

          <!-- Loading skeletons -->
          <template v-if="mapStore.loading">
            <div v-for="i in 4" :key="i" class="rounded-lg border border-gray-200 overflow-hidden">
              <div class="skeleton h-40"></div>
              <div class="p-3 space-y-2">
                <div class="skeleton h-5 w-24"></div>
                <div class="skeleton h-4 w-40"></div>
                <div class="skeleton h-3 w-32"></div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- List panel toggle (when collapsed) -->
      <button
        v-if="!mapStore.showListPanel"
        @click="mapStore.showListPanel = true"
        class="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-white rounded-r-lg shadow-lg border border-gray-200 px-1 py-4 text-gray-400 hover:text-gray-600 hidden lg:block"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>

      <!-- Map -->
      <div class="flex-1 relative">
        <PropertyMap />

        <!-- Save search button -->
        <button
          v-if="authStore.isAuthenticated"
          @click="showSaveSearch = true"
          class="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 bg-white shadow-lg rounded-full px-5 py-2.5 text-sm font-medium text-primary-600 hover:bg-primary-50 border border-gray-200 transition-colors"
        >
          Save This Search
        </button>

        <!-- Save search modal -->
        <div v-if="showSaveSearch" class="absolute inset-0 z-20 flex items-center justify-center bg-black/30">
          <div class="bg-white rounded-xl shadow-xl p-6 w-96 mx-4">
            <h3 class="text-lg font-semibold mb-4">Save Search</h3>
            <input
              v-model="searchName"
              type="text"
              placeholder="Name this search (e.g. 'Downtown Condos under $800K')"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3"
            />
            <label class="flex items-center gap-2 text-sm text-gray-600 mb-4">
              <input v-model="emailAlerts" type="checkbox" class="rounded border-gray-300 text-primary-600" />
              Email me new listings matching this search
            </label>
            <div class="flex gap-2">
              <button @click="showSaveSearch = false" class="flex-1 border border-gray-300 rounded-lg py-2 text-sm text-gray-700 hover:bg-gray-50">Cancel</button>
              <button @click="handleSaveSearch" class="flex-1 bg-primary-600 text-white rounded-lg py-2 text-sm hover:bg-primary-700">Save</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMapStore } from '@/store/map'
import { useAuthStore } from '@/store/auth'
import { createSavedSearch } from '@/api/user'
import FilterPanel from '@/components/search/FilterPanel.vue'
import PropertyMap from '@/components/map/PropertyMap.vue'
import PropertyCard from '@/components/property/PropertyCard.vue'
import type { GeoJSONFeature, Property } from '@/types'

const mapStore = useMapStore()
const authStore = useAuthStore()

const showSaveSearch = ref(false)
const searchName = ref('')
const emailAlerts = ref(true)

const listingCards = computed(() => mapStore.listings.slice(0, 50))

function featureToProperty(feature: GeoJSONFeature): Property {
  const p = feature.properties
  return {
    id: p.id,
    mls_number: p.mls,
    status: p.status as Property['status'],
    property_type: p.type,
    list_price: p.status === 'sold' ? 0 : p.price,
    sold_price: p.status === 'sold' ? p.price : null,
    bedrooms: p.beds,
    bathrooms: p.baths,
    street_number: '',
    street_name: p.address,
    unit_number: null,
    city: '',
    province: 'ON',
    postal_code: '',
    neighborhood: null,
    municipality: null,
    municipality_code: null,
    latitude: feature.geometry.coordinates[1],
    longitude: feature.geometry.coordinates[0],
    bedrooms_plus: 0,
    parking_spaces: 0,
    interior_sqft: typeof p.sqft === 'number' ? p.sqft : null,
    sqft_range: typeof p.sqft === 'string' ? p.sqft : null,
    year_built: null,
    original_price: null,
    photos: p.photo ? [p.photo] : [],
    days_on_market: p.days_on_market,
    list_date: null,
    sold_date: null,
  }
}

async function handleSaveSearch() {
  if (!searchName.value.trim()) return

  await createSavedSearch({
    name: searchName.value,
    filters: { ...mapStore.filters },
    bounds: {
      sw_lat: mapStore.bounds.sw_lat,
      sw_lng: mapStore.bounds.sw_lng,
      ne_lat: mapStore.bounds.ne_lat,
      ne_lng: mapStore.bounds.ne_lng,
    },
    email_alerts: emailAlerts.value,
    alert_frequency: 'daily',
  })

  showSaveSearch.value = false
  searchName.value = ''
}
</script>
