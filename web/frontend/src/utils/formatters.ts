/**
 * Format price as currency: $1,250,000
 */
export function formatPrice(price: number): string {
  if (price >= 1_000_000) {
    const m = price / 1_000_000
    return m % 1 === 0 ? `$${m}M` : `$${m.toFixed(1)}M`
  }
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(price)
}

/**
 * Format price for map pin: $1.2M or $850K
 */
export function formatPriceShort(price: number): string {
  if (price >= 1_000_000) {
    return `$${(price / 1_000_000).toFixed(1)}M`
  }
  if (price >= 1_000) {
    return `$${Math.round(price / 1_000)}K`
  }
  return `$${price}`
}

/**
 * Format number with commas: 1,250,000
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-CA').format(num)
}

/**
 * Format date: Jan 15, 2024
 */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Format relative time: "3 days ago", "2 months ago"
 */
export function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 30) return `${days} days ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return `${Math.floor(days / 365)} years ago`
}

/**
 * Format sqft: "1,250 sqft" or "1,000-1,199 sqft"
 */
export function formatSqft(sqft: number | string | null): string {
  if (!sqft) return 'N/A'
  if (typeof sqft === 'string') return `${sqft} sqft`
  return `${formatNumber(sqft)} sqft`
}

/**
 * Property type display name
 */
export function formatPropertyType(type: string): string {
  const map: Record<string, string> = {
    'detached': 'Detached',
    'semi-detached': 'Semi-Detached',
    'townhouse': 'Townhouse',
    'condo-apt': 'Condo',
    'condo-townhouse': 'Condo Town',
    'duplex': 'Duplex',
    'triplex': 'Triplex',
    'multiplex': 'Multiplex',
    'vacant-land': 'Land',
    'farm': 'Farm',
    'commercial': 'Commercial',
  }
  return map[type] || type
}
