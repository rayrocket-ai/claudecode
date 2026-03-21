import api from './client'
import type { MapFilters, PropertyDetail, SearchResult, AutocompleteResult, PriceHistoryResponse } from '@/types'

export async function fetchMapListings(params: {
  sw_lat: number
  sw_lng: number
  ne_lat: number
  ne_lng: number
  zoom: number
  status?: string
  property_type?: string
  price_min?: number
  price_max?: number
  beds_min?: number
  baths_min?: number
  sold_within_days?: number
}) {
  const { data } = await api.get('/map/listings', { params })
  return data
}

export async function fetchMapClusters(params: {
  sw_lat: number
  sw_lng: number
  ne_lat: number
  ne_lng: number
  zoom: number
  status?: string
  property_type?: string
  price_min?: number
  price_max?: number
  beds_min?: number
}) {
  const { data } = await api.get('/map/clusters', { params })
  return data
}

export async function fetchBoundaries(type: string) {
  const { data } = await api.get(`/map/boundaries/${type}`)
  return data
}

export async function searchProperties(filters: MapFilters): Promise<SearchResult> {
  const { data } = await api.get('/search', { params: filters })
  return data
}

export async function fetchProperty(id: number): Promise<PropertyDetail> {
  const { data } = await api.get(`/properties/${id}`)
  return data.data
}

export async function fetchPropertyByMls(mls: string): Promise<PropertyDetail> {
  const { data } = await api.get(`/properties/mls/${mls}`)
  return data.data
}

export async function fetchPriceHistory(id: number): Promise<PriceHistoryResponse> {
  const { data } = await api.get(`/properties/${id}/history`)
  return data
}

export async function fetchSimilarProperties(id: number) {
  const { data } = await api.get(`/properties/${id}/similar`)
  return data.data
}

export async function autocomplete(q: string): Promise<AutocompleteResult[]> {
  const { data } = await api.get('/autocomplete', { params: { q } })
  return data.data
}
