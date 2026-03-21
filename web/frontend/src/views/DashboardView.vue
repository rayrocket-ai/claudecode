<template>
  <div class="max-w-4xl mx-auto p-6 overflow-y-auto h-full">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Saved Searches</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ savedSearches.length }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Favorites</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ favoriteCount }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <p class="text-sm text-gray-500">Unread Alerts</p>
        <p class="text-3xl font-bold text-gray-900 mt-1">{{ unreadAlerts }}</p>
      </div>
    </div>

    <!-- Recent alerts -->
    <section class="mb-8">
      <h2 class="text-lg font-semibold text-gray-900 mb-3">Recent Alerts</h2>
      <div v-if="alerts.length" class="space-y-2">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          :class="['border rounded-lg p-3 flex items-center gap-3', alert.is_read ? 'border-gray-200 bg-white' : 'border-primary-200 bg-primary-50']"
        >
          <span :class="['w-2 h-2 rounded-full shrink-0', alert.is_read ? 'bg-gray-300' : 'bg-primary-500']"></span>
          <div class="min-w-0 flex-1">
            <p class="text-sm text-gray-900 truncate">
              <span class="font-medium">{{ alert.alert_type.replace('-', ' ') }}</span>
              — {{ alert.property?.short_address }}
            </p>
            <p class="text-xs text-gray-500">{{ alert.saved_search?.name }}</p>
          </div>
          <router-link
            v-if="alert.property"
            :to="{ name: 'property', params: { id: alert.property.id } }"
            class="text-xs text-primary-600 hover:text-primary-700 shrink-0"
          >View</router-link>
        </div>
      </div>
      <p v-else class="text-sm text-gray-400">No alerts yet. Save a search to get notified.</p>
    </section>

    <!-- Recently viewed -->
    <section>
      <h2 class="text-lg font-semibold text-gray-900 mb-3">Recently Viewed</h2>
      <div v-if="recentlyViewed.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <router-link
          v-for="item in recentlyViewed"
          :key="item.property.id"
          :to="{ name: 'property', params: { id: item.property.id } }"
          class="flex gap-3 p-3 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
        >
          <img v-if="item.property.photos?.[0]" :src="item.property.photos[0]" class="w-20 h-20 rounded object-cover shrink-0" />
          <div class="min-w-0">
            <p class="font-medium text-gray-900">{{ formatPrice(item.property.list_price) }}</p>
            <p class="text-sm text-gray-500 truncate">{{ item.property.short_address }}</p>
            <p class="text-xs text-gray-400 mt-1">Viewed {{ formatRelativeTime(item.viewed_at) }}</p>
          </div>
        </router-link>
      </div>
      <p v-else class="text-sm text-gray-400">No properties viewed yet.</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchSavedSearches, fetchFavorites, fetchAlerts } from '@/api/user'
import { formatPrice, formatRelativeTime } from '@/utils/formatters'
import api from '@/api/client'

const savedSearches = ref<unknown[]>([])
const favoriteCount = ref(0)
const unreadAlerts = ref(0)
const alerts = ref<unknown[]>([])
const recentlyViewed = ref<unknown[]>([])

onMounted(async () => {
  const [searches, favs, alertsData, viewed] = await Promise.all([
    fetchSavedSearches(),
    fetchFavorites(),
    fetchAlerts(),
    api.get('/recently-viewed').then(r => r.data.data),
  ])
  savedSearches.value = searches
  favoriteCount.value = favs.total || favs.data?.length || 0
  alerts.value = alertsData.data || []
  unreadAlerts.value = alerts.value.filter((a: { is_read: boolean }) => !a.is_read).length
  recentlyViewed.value = viewed || []
})
</script>
