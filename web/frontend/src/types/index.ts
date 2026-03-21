export interface Property {
  id: number
  mls_number: string
  status: 'for-sale' | 'sold' | 'terminated' | 'leased'
  property_type: string
  street_number: string
  street_name: string
  unit_number: string | null
  city: string
  province: string
  postal_code: string
  neighborhood: string | null
  municipality: string | null
  municipality_code: number | null
  latitude: number
  longitude: number
  list_price: number
  sold_price: number | null
  original_price: number | null
  bedrooms: number
  bedrooms_plus: number
  bathrooms: number
  parking_spaces: number
  interior_sqft: number | null
  sqft_range: string | null
  year_built: number | null
  photos: string[]
  days_on_market: number | null
  list_date: string | null
  sold_date: string | null
}

export interface PropertyDetail extends Property {
  full_address: string
  short_address: string
  sold_to_list_ratio: number | null
  is_favorited: boolean
  description: string | null
  maintenance_fee: number | null
  annual_taxes: number | null
  basement: string | null
  heating: string | null
  cooling: string | null
  exterior: string | null
  stories: number | null
  lot_size_sqft: number | null
  lot_size_frontage: string | null
  lot_size_depth: string | null
  style: string | null
  garage_type: string | null
  listing_agent_name: string | null
  listing_brokerage: string | null
  virtual_tour_url: string | null
  legal_description: string | null
  zoning: string | null
  price_history: PriceHistoryEvent[]
}

export interface PriceHistoryEvent {
  id: number
  event_type: string
  price: number
  previous_price: number | null
  event_date: string
}

export interface PriceHistoryResponse {
  current: PriceHistoryEvent[]
  address_history: PropertyDetail[]
}

export interface MapFilters {
  status?: string
  property_type?: string
  price_min?: number
  price_max?: number
  beds_min?: number
  baths_min?: number
  city?: string
  neighborhood?: string
  municipality_code?: number
  sort_by?: string
  sort_dir?: string
  sold_within_days?: number
  keywords?: string
  limit?: number
  page?: number
}

export interface MapCluster {
  lat: number
  lng: number
  count: number
  avg_price: number
  min_price: number
  max_price: number
}

export interface GeoJSONFeature {
  type: 'Feature'
  geometry: {
    type: 'Point'
    coordinates: [number, number]
  }
  properties: {
    id: number
    mls: string
    price: number
    beds: number
    baths: number
    type: string
    status: string
    address: string
    photo: string | null
    sqft: string | number | null
    days_on_market: number | null
  }
}

export interface SearchResult {
  data: Property[]
  current_page: number
  total: number
  per_page: number
  last_page: number
}

export interface AutocompleteResult {
  type: 'city' | 'neighborhood' | 'address'
  label: string
  value: string
  id?: number
  city?: string
  count?: number
}

export interface SavedSearch {
  id: number
  name: string
  filters: MapFilters
  bounds: { sw_lat: number; sw_lng: number; ne_lat: number; ne_lng: number } | null
  city: string | null
  neighborhood: string | null
  email_alerts: boolean
  alert_frequency: string
  created_at: string
}

export interface User {
  id: number
  name: string
  email: string
  phone: string | null
  avatar_url: string | null
  role: 'user' | 'agent' | 'admin'
  preferences: Record<string, unknown> | null
}
