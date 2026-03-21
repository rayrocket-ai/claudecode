<template>
  <div v-if="loading" class="max-w-6xl mx-auto p-6">
    <div class="skeleton h-8 w-48 mb-4"></div>
    <div class="skeleton h-96 w-full rounded-xl mb-4"></div>
    <div class="grid grid-cols-3 gap-4">
      <div class="skeleton h-24 rounded-lg" v-for="i in 3" :key="i"></div>
    </div>
  </div>

  <div v-else-if="property" class="max-w-6xl mx-auto p-6 overflow-y-auto h-full custom-scrollbar">
    <!-- Back button -->
    <button @click="router.back()" class="text-sm text-primary-600 hover:text-primary-700 mb-4 flex items-center gap-1">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
      Back to map
    </button>

    <!-- Photo gallery -->
    <div class="grid grid-cols-4 gap-2 rounded-xl overflow-hidden h-96 mb-6">
      <div class="col-span-2 row-span-2 bg-gray-200">
        <img v-if="property.photos?.[0]" :src="property.photos[0]" class="w-full h-full object-cover" />
      </div>
      <div v-for="(photo, i) in property.photos?.slice(1, 5)" :key="i" class="bg-gray-200">
        <img :src="photo" class="w-full h-full object-cover" />
      </div>
    </div>

    <!-- Header: price + address + actions -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <div class="flex items-center gap-3 mb-1">
          <span :class="['px-2 py-0.5 rounded text-xs font-medium', property.status === 'sold' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700']">
            {{ property.status === 'sold' ? 'SOLD' : 'FOR SALE' }}
          </span>
          <span class="text-xs text-gray-500">MLS# {{ property.mls_number }}</span>
        </div>
        <h1 class="text-3xl font-bold text-gray-900">
          {{ formatPrice(property.status === 'sold' ? property.sold_price! : property.list_price) }}
        </h1>
        <p v-if="property.status === 'sold' && property.sold_to_list_ratio" class="text-sm text-gray-500">
          {{ property.sold_to_list_ratio }}% of asking ({{ formatPrice(property.list_price) }})
        </p>
        <p class="text-lg text-gray-700 mt-1">{{ property.full_address }}</p>
      </div>

      <div class="flex gap-2">
        <button
          @click="handleFavorite"
          :class="['px-4 py-2 rounded-lg border text-sm font-medium transition-colors', property.is_favorited ? 'bg-red-50 text-red-600 border-red-200' : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400']"
        >
          {{ property.is_favorited ? 'Saved' : 'Save' }}
        </button>
        <button class="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:border-primary-400">
          Share
        </button>
      </div>
    </div>

    <!-- Key stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
      <div class="bg-gray-50 rounded-lg p-3 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ property.bedrooms }}</p>
        <p class="text-xs text-gray-500">Bedrooms</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ property.bathrooms }}</p>
        <p class="text-xs text-gray-500">Bathrooms</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ property.sqft_range || property.interior_sqft || 'N/A' }}</p>
        <p class="text-xs text-gray-500">Sqft</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ property.parking_spaces || 0 }}</p>
        <p class="text-xs text-gray-500">Parking</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ property.year_built || 'N/A' }}</p>
        <p class="text-xs text-gray-500">Year Built</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ property.days_on_market ?? 'N/A' }}</p>
        <p class="text-xs text-gray-500">Days on Market</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left: Details -->
      <div class="lg:col-span-2 space-y-8">
        <!-- Description -->
        <section v-if="property.description">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">Description</h2>
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{{ property.description }}</p>
        </section>

        <!-- Property Details table -->
        <section>
          <h2 class="text-lg font-semibold text-gray-900 mb-3">Property Details</h2>
          <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <DetailRow label="Type" :value="formatPropertyType(property.property_type)" />
            <DetailRow label="Style" :value="property.style" />
            <DetailRow label="Lot Size" :value="property.lot_size_sqft ? `${formatNumber(property.lot_size_sqft)} sqft` : property.lot_size_frontage ? `${property.lot_size_frontage} x ${property.lot_size_depth}` : null" />
            <DetailRow label="Stories" :value="property.stories" />
            <DetailRow label="Basement" :value="property.basement" />
            <DetailRow label="Heating" :value="property.heating" />
            <DetailRow label="Cooling" :value="property.cooling" />
            <DetailRow label="Exterior" :value="property.exterior" />
            <DetailRow label="Garage" :value="property.garage_type" />
            <DetailRow label="Taxes" :value="property.annual_taxes ? formatPrice(property.annual_taxes) + '/yr' : null" />
            <DetailRow v-if="property.maintenance_fee" label="Maint. Fee" :value="`${formatPrice(property.maintenance_fee)}/mo`" />
            <DetailRow label="Zoning" :value="property.zoning" />
          </div>
        </section>

        <!-- Price History chart -->
        <section v-if="property.price_history?.length">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">Price History</h2>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-2 text-left text-gray-500 font-medium">Date</th>
                  <th class="px-4 py-2 text-left text-gray-500 font-medium">Event</th>
                  <th class="px-4 py-2 text-right text-gray-500 font-medium">Price</th>
                  <th class="px-4 py-2 text-right text-gray-500 font-medium">Change</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in property.price_history" :key="event.id" class="border-t border-gray-100">
                  <td class="px-4 py-2 text-gray-600">{{ formatDate(event.event_date) }}</td>
                  <td class="px-4 py-2">
                    <span :class="eventBadgeClass(event.event_type)">{{ event.event_type }}</span>
                  </td>
                  <td class="px-4 py-2 text-right font-medium">{{ formatPrice(event.price) }}</td>
                  <td class="px-4 py-2 text-right">
                    <span v-if="event.previous_price" :class="event.price > event.previous_price ? 'text-green-600' : 'text-red-600'">
                      {{ event.price > event.previous_price ? '+' : '' }}{{ formatPrice(event.price - event.previous_price) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <!-- Right sidebar -->
      <div class="space-y-6">
        <!-- Mini map -->
        <div class="bg-gray-200 rounded-lg h-48 overflow-hidden">
          <div ref="miniMapContainer" class="w-full h-full"></div>
        </div>

        <!-- Listing agent -->
        <div v-if="property.listing_agent_name" class="border border-gray-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-2">Listed By</h3>
          <p class="text-sm text-gray-700">{{ property.listing_agent_name }}</p>
          <p class="text-xs text-gray-500">{{ property.listing_brokerage }}</p>
        </div>

        <!-- Similar properties -->
        <div v-if="similarProperties.length">
          <h3 class="text-sm font-semibold text-gray-900 mb-3">Similar Properties</h3>
          <div class="space-y-3">
            <router-link
              v-for="sim in similarProperties.slice(0, 4)"
              :key="sim.id"
              :to="{ name: 'property', params: { id: sim.id } }"
              class="flex gap-3 p-2 rounded-lg hover:bg-gray-50"
            >
              <img v-if="sim.photo" :src="sim.photo" class="w-16 h-16 rounded object-cover shrink-0" />
              <div class="min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ formatPrice(sim.price) }}</p>
                <p class="text-xs text-gray-500 truncate">{{ sim.address }}, {{ sim.city }}</p>
                <p class="text-xs text-gray-400">{{ sim.beds }}bd / {{ sim.baths }}ba</p>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import mapboxgl from 'mapbox-gl'
import { fetchProperty, fetchSimilarProperties } from '@/api/listings'
import { toggleFavorite } from '@/api/user'
import { useAuthStore } from '@/store/auth'
import { formatPrice, formatDate, formatPropertyType, formatNumber } from '@/utils/formatters'
import type { PropertyDetail } from '@/types'

interface SimilarProperty {
  id: number
  address: string
  city: string
  price: number
  beds: number
  baths: number
  photo: string | null
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const property = ref<PropertyDetail | null>(null)
const similarProperties = ref<SimilarProperty[]>([])
const loading = ref(true)
const miniMapContainer = ref<HTMLElement>()

onMounted(async () => {
  const id = parseInt(route.params.id as string)
  try {
    property.value = await fetchProperty(id)
    similarProperties.value = await fetchSimilarProperties(id)

    // Init mini map
    if (miniMapContainer.value && property.value) {
      const miniMap = new mapboxgl.Map({
        container: miniMapContainer.value,
        style: 'mapbox://styles/mapbox/light-v11',
        center: [property.value.longitude, property.value.latitude],
        zoom: 15,
        interactive: false,
      })
      new mapboxgl.Marker({ color: '#2563eb' })
        .setLngLat([property.value.longitude, property.value.latitude])
        .addTo(miniMap)
    }
  } catch (error) {
    console.error('Failed to load property:', error)
  } finally {
    loading.value = false
  }
})

async function handleFavorite() {
  if (!authStore.isAuthenticated || !property.value) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  await toggleFavorite(property.value.id, property.value.is_favorited)
  property.value.is_favorited = !property.value.is_favorited
}

function eventBadgeClass(type: string): string {
  const base = 'px-2 py-0.5 rounded text-xs font-medium'
  switch (type) {
    case 'listed': return `${base} bg-green-100 text-green-700`
    case 'sold': return `${base} bg-red-100 text-red-700`
    case 'price-change': return `${base} bg-yellow-100 text-yellow-700`
    case 'terminated': return `${base} bg-gray-100 text-gray-700`
    default: return `${base} bg-blue-100 text-blue-700`
  }
}

// Simple detail row component
const DetailRow = {
  props: { label: String, value: [String, Number, null] },
  template: `
    <div v-if="value" class="flex justify-between py-1 border-b border-gray-50">
      <span class="text-gray-500">{{ label }}</span>
      <span class="text-gray-900 font-medium">{{ value }}</span>
    </div>
  `,
}
</script>
