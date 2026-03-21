import { defineStore } from 'pinia'
import { ref, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchMapListings } from '@/api/listings'
import type { MapFilters, GeoJSONFeature, MapCluster } from '@/types'

export const useMapStore = defineStore('map', () => {
  const route = useRoute()
  const router = useRouter()

  // Map viewport state
  const center = reactive({ lat: 43.6532, lng: -79.3832 }) // Toronto default
  const zoom = ref(12)
  const bounds = reactive({
    sw_lat: 0, sw_lng: 0, ne_lat: 0, ne_lng: 0,
  })

  // Filters
  const filters = reactive<MapFilters>({
    status: 'for-sale',
    property_type: undefined,
    price_min: undefined,
    price_max: undefined,
    beds_min: undefined,
    baths_min: undefined,
    sold_within_days: undefined,
  })

  // Data
  const listings = ref<GeoJSONFeature[]>([])
  const clusters = ref<MapCluster[]>([])
  const displayMode = ref<'geojson' | 'clusters'>('geojson')
  const loading = ref(false)
  const selectedPropertyId = ref<number | null>(null)
  const showListPanel = ref(true)
  const totalResults = ref(0)

  // Fetch listings based on current viewport and filters
  async function loadListings() {
    if (!bounds.sw_lat) return

    loading.value = true
    try {
      const params = {
        sw_lat: bounds.sw_lat,
        sw_lng: bounds.sw_lng,
        ne_lat: bounds.ne_lat,
        ne_lng: bounds.ne_lng,
        zoom: zoom.value,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== undefined && v !== null)
        ),
      }

      const result = await fetchMapListings(params)

      if (result.type === 'clusters') {
        displayMode.value = 'clusters'
        clusters.value = result.data
        listings.value = []
      } else {
        displayMode.value = 'geojson'
        listings.value = result.data.features || []
        clusters.value = []
        totalResults.value = result.pagination?.total ?? listings.value.length
      }
    } catch (error) {
      console.error('Failed to load listings:', error)
    } finally {
      loading.value = false
    }
  }

  // Update bounds when map moves
  function updateBounds(sw: { lat: number; lng: number }, ne: { lat: number; lng: number }, newZoom: number) {
    bounds.sw_lat = sw.lat
    bounds.sw_lng = sw.lng
    bounds.ne_lat = ne.lat
    bounds.ne_lng = ne.lng
    zoom.value = newZoom
    center.lat = (sw.lat + ne.lat) / 2
    center.lng = (sw.lng + ne.lng) / 2

    // Sync to URL
    syncToUrl()
    loadListings()
  }

  function updateFilters(newFilters: Partial<MapFilters>) {
    Object.assign(filters, newFilters)
    syncToUrl()
    loadListings()
  }

  function selectProperty(id: number | null) {
    selectedPropertyId.value = id
  }

  // Sync map state to URL params
  function syncToUrl() {
    const query: Record<string, string> = {
      lat: center.lat.toFixed(6),
      lon: center.lng.toFixed(6),
      zoom: zoom.value.toFixed(1),
    }

    if (filters.status && filters.status !== 'for-sale') query.status = filters.status
    if (filters.property_type) query.type = filters.property_type
    if (filters.price_min) query.price_min = String(filters.price_min)
    if (filters.price_max) query.price_max = String(filters.price_max)
    if (filters.beds_min) query.beds = String(filters.beds_min)
    if (filters.baths_min) query.baths = String(filters.baths_min)

    router.replace({ query })
  }

  // Hydrate from URL params
  function hydrateFromUrl() {
    const q = route.query
    if (q.lat) center.lat = parseFloat(q.lat as string)
    if (q.lon) center.lng = parseFloat(q.lon as string)
    if (q.zoom) zoom.value = parseFloat(q.zoom as string)
    if (q.status) filters.status = q.status as string
    if (q.type) filters.property_type = q.type as string
    if (q.price_min) filters.price_min = parseInt(q.price_min as string)
    if (q.price_max) filters.price_max = parseInt(q.price_max as string)
    if (q.beds) filters.beds_min = parseInt(q.beds as string)
    if (q.baths) filters.baths_min = parseInt(q.baths as string)
  }

  return {
    center, zoom, bounds, filters,
    listings, clusters, displayMode,
    loading, selectedPropertyId, showListPanel, totalResults,
    loadListings, updateBounds, updateFilters, selectProperty,
    hydrateFromUrl, syncToUrl,
  }
})
