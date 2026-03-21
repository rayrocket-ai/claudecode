<template>
  <div ref="mapContainer" class="w-full h-full relative">
    <!-- Loading overlay -->
    <div v-if="mapStore.loading" class="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-white rounded-full shadow-lg px-4 py-2 flex items-center gap-2">
      <div class="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
      <span class="text-sm text-gray-600">Loading...</span>
    </div>

    <!-- Map controls -->
    <div class="absolute top-4 right-4 z-10 flex flex-col gap-2">
      <button @click="zoomIn" class="w-9 h-9 bg-white rounded-lg shadow-md flex items-center justify-center text-gray-700 hover:bg-gray-50">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v12m6-6H6" /></svg>
      </button>
      <button @click="zoomOut" class="w-9 h-9 bg-white rounded-lg shadow-md flex items-center justify-center text-gray-700 hover:bg-gray-50">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 12H6" /></svg>
      </button>
      <button @click="toggleStyle" class="w-9 h-9 bg-white rounded-lg shadow-md flex items-center justify-center text-gray-700 hover:bg-gray-50 text-xs font-bold">
        {{ isSatellite ? 'Map' : 'Sat' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import mapboxgl from 'mapbox-gl'
import { useMapStore } from '@/store/map'
import { useRouter } from 'vue-router'
import { formatPriceShort } from '@/utils/formatters'
import type { GeoJSONFeature, MapCluster } from '@/types'

const mapStore = useMapStore()
const router = useRouter()
const mapContainer = ref<HTMLElement>()
const isSatellite = ref(false)

let map: mapboxgl.Map | null = null
let clusterMarkers: mapboxgl.Marker[] = []
let priceMarkers: mapboxgl.Marker[] = []

// Mapbox access token — replace with your own or use self-hosted tiles
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || 'your_mapbox_token_here'

onMounted(() => {
  if (!mapContainer.value) return

  mapStore.hydrateFromUrl()

  map = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/mapbox/light-v11',
    center: [mapStore.center.lng, mapStore.center.lat],
    zoom: mapStore.zoom,
    minZoom: 8,
    maxZoom: 18,
    attributionControl: false,
  })

  map.addControl(new mapboxgl.AttributionControl({ compact: true }), 'bottom-left')

  map.on('load', () => {
    onMapMoveEnd()
  })

  map.on('moveend', () => {
    onMapMoveEnd()
  })
})

onUnmounted(() => {
  map?.remove()
})

function onMapMoveEnd() {
  if (!map) return

  const bounds = map.getBounds()
  const sw = bounds.getSouthWest()
  const ne = bounds.getNorthEast()
  const z = map.getZoom()

  mapStore.updateBounds(
    { lat: sw.lat, lng: sw.lng },
    { lat: ne.lat, lng: ne.lng },
    z
  )
}

// Watch for listing data changes and render on map
watch(() => mapStore.listings, (features) => {
  renderPricePins(features)
}, { deep: true })

watch(() => mapStore.clusters, (clusters) => {
  renderClusterMarkers(clusters)
}, { deep: true })

function renderPricePins(features: GeoJSONFeature[]) {
  // Clear old markers
  priceMarkers.forEach(m => m.remove())
  priceMarkers = []
  clusterMarkers.forEach(m => m.remove())
  clusterMarkers = []

  features.forEach((feature) => {
    const { coordinates } = feature.geometry
    const { id, price, status, beds, baths, address } = feature.properties

    // Create price pin element
    const el = document.createElement('div')
    el.className = `price-pin ${status === 'sold' ? 'sold' : ''}`
    el.textContent = formatPriceShort(price)
    el.title = `${address} — ${beds}bd/${baths}ba`

    el.addEventListener('click', () => {
      mapStore.selectProperty(id)
      showPopup(feature)
    })

    const marker = new mapboxgl.Marker({ element: el })
      .setLngLat([coordinates[0], coordinates[1]])
      .addTo(map!)

    priceMarkers.push(marker)
  })
}

function renderClusterMarkers(clusters: MapCluster[]) {
  // Clear old markers
  clusterMarkers.forEach(m => m.remove())
  clusterMarkers = []
  priceMarkers.forEach(m => m.remove())
  priceMarkers = []

  clusters.forEach((cluster) => {
    const el = document.createElement('div')
    const size = Math.max(36, Math.min(60, 36 + cluster.count * 0.5))
    el.className = 'cluster-marker'
    el.style.width = `${size}px`
    el.style.height = `${size}px`
    el.style.fontSize = cluster.count > 99 ? '11px' : '13px'
    el.textContent = cluster.count > 999 ? `${(cluster.count / 1000).toFixed(1)}k` : String(cluster.count)
    el.title = `${cluster.count} listings — Avg ${formatPriceShort(cluster.avg_price)}`

    el.addEventListener('click', () => {
      map?.flyTo({
        center: [cluster.lng, cluster.lat],
        zoom: (map?.getZoom() ?? 10) + 2,
        duration: 500,
      })
    })

    const marker = new mapboxgl.Marker({ element: el })
      .setLngLat([cluster.lng, cluster.lat])
      .addTo(map!)

    clusterMarkers.push(marker)
  })
}

function showPopup(feature: GeoJSONFeature) {
  if (!map) return

  const { coordinates } = feature.geometry
  const p = feature.properties
  const priceDisplay = formatPriceShort(p.price)

  const html = `
    <div class="cursor-pointer" onclick="window.__navigateProperty(${p.id})">
      ${p.photo ? `<img src="${p.photo}" class="w-full h-36 object-cover" alt="${p.address}" />` : '<div class="w-full h-36 bg-gray-200 flex items-center justify-center text-gray-400 text-sm">No Photo</div>'}
      <div class="p-3">
        <p class="text-lg font-bold text-gray-900">${priceDisplay}</p>
        <p class="text-sm text-gray-600">${p.address}</p>
        <div class="flex gap-3 mt-1 text-xs text-gray-500">
          <span>${p.beds} bed</span>
          <span>${p.baths} bath</span>
          ${p.sqft ? `<span>${p.sqft} sqft</span>` : ''}
          ${p.days_on_market !== null ? `<span>${p.days_on_market}d on market</span>` : ''}
        </div>
      </div>
    </div>
  `

  new mapboxgl.Popup({ offset: 25, maxWidth: '300px' })
    .setLngLat([coordinates[0], coordinates[1]])
    .setHTML(html)
    .addTo(map)
}

// Global navigation handler for popup clicks
if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).__navigateProperty = (id: number) => {
    router.push({ name: 'property', params: { id } })
  }
}

function zoomIn() { map?.zoomIn({ duration: 300 }) }
function zoomOut() { map?.zoomOut({ duration: 300 }) }

function toggleStyle() {
  if (!map) return
  isSatellite.value = !isSatellite.value
  map.setStyle(isSatellite.value
    ? 'mapbox://styles/mapbox/satellite-streets-v12'
    : 'mapbox://styles/mapbox/light-v11'
  )
}
</script>
