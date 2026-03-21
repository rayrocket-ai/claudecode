import api from './client'

export async function login(email: string, password: string) {
  const { data } = await api.post('/auth/login', { email, password })
  return data
}

export async function register(name: string, email: string, password: string, passwordConfirmation: string) {
  const { data } = await api.post('/auth/register', {
    name,
    email,
    password,
    password_confirmation: passwordConfirmation,
  })
  return data
}

export async function logout() {
  await api.post('/auth/logout')
}

export async function fetchProfile() {
  const { data } = await api.get('/user')
  return data.data
}

export async function toggleFavorite(propertyId: number, isFavorited: boolean) {
  if (isFavorited) {
    await api.delete(`/favorites/${propertyId}`)
  } else {
    await api.post(`/favorites/${propertyId}`)
  }
}

export async function fetchFavorites(page = 1) {
  const { data } = await api.get('/favorites', { params: { page } })
  return data
}

export async function fetchSavedSearches() {
  const { data } = await api.get('/saved-searches')
  return data.data
}

export async function createSavedSearch(params: {
  name: string
  filters: Record<string, unknown>
  bounds?: { sw_lat: number; sw_lng: number; ne_lat: number; ne_lng: number }
  city?: string
  neighborhood?: string
  email_alerts?: boolean
  alert_frequency?: string
}) {
  const { data } = await api.post('/saved-searches', params)
  return data.data
}

export async function deleteSavedSearch(id: number) {
  await api.delete(`/saved-searches/${id}`)
}

export async function fetchAlerts(page = 1) {
  const { data } = await api.get('/alerts', { params: { page } })
  return data
}

export async function fetchMarketTrends(params: { city?: string; months?: number; property_type?: string }) {
  const { data } = await api.get('/stats/market-trends', { params })
  return data.data
}
