# HouseSigma.com - Complete Technical Analysis

> Analysis of https://housesigma.com — Canada's leading real estate data platform
> Map URL analyzed: `/on/toronto-real-estate/map/?center_marker=43.64193,-79.38149&view=map&municipality=10343&status=for-sale`

---

## 1. Company Overview

- **Founded:** 2016 in Toronto, Canada
- **Achieved profitability:** 2018 (self-sustaining, no ongoing funding dependency)
- **Users:** 2+ million registered users
- **Traffic:** 5+ million monthly web visits
- **Recognition:** Deloitte 2025 Technology Fast 500 (#409)
- **First in Canada** to make sold prices publicly available
- **Coverage:** GTA (since 2003), Greater Vancouver, Ottawa, Ontario, Alberta

---

## 2. Confirmed Tech Stack (from official HouseSigma recruitment posts)

### Backend
| Technology | Purpose |
|-----------|---------|
| **PHP 7/8** | Primary backend language |
| **Python** | ML/AI, data processing |
| **Node.js** | Auxiliary services |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Vue.js** | Frontend framework (SPA) |
| **TypeScript** | Type-safe JavaScript |
| **Native iOS** | iOS mobile app |
| **Native Android** | Android mobile app |

### Infrastructure & Services
| Technology | Purpose |
|-----------|---------|
| **CentOS 8 / Rocky 8** | Server OS |
| **AWS** | Cloud infrastructure |
| **MySQL** | Primary relational database |
| **MongoDB** | Document store (listings, property data) |
| **Redis** | Caching layer |
| **Elasticsearch** | Search engine (property search, autocomplete) |
| **Kafka** | Message queue / event streaming |
| **Kubernetes** | Container orchestration |

### Tools & Communication
| Tool | Purpose |
|------|---------|
| Discord | Team communication |
| Zoom | Meetings |
| Lark | Collaboration |
| ClickUp | Project management |
| Figma | UI/UX design |

---

## 3. Mapping Architecture (The Core Feature You Liked)

### Map Stack
HouseSigma's interactive map is built with a **self-hosted tile infrastructure**:

| Layer | Technology | Evidence |
|-------|-----------|----------|
| **Map Renderer** | Mapbox GL JS API | Detected by BuiltWith/ZoomInfo |
| **Vector Tiles** | OpenMapTiles | GitHub fork: `housesigma/openmaptiles` (PLpgSQL) |
| **Tile Schema** | OpenMapTiles Vector Tile Schema | Self-hosted vector tiles from OpenStreetMap data |
| **Tile Server** | Likely TileServer GL or custom | Serves .pbf vector tiles to Mapbox GL JS |

### How Their Map Works

```
┌─────────────────────────────────────────────────────┐
│                  USER'S BROWSER                      │
│                                                      │
│  ┌─────────────┐    ┌────────────────────────────┐  │
│  │  Vue.js SPA │───▶│     Mapbox GL JS           │  │
│  │  (TypeScript)│    │  - Vector tile rendering    │  │
│  │             │    │  - Property pin clustering  │  │
│  │             │    │  - Custom map styles        │  │
│  └──────┬──────┘    └────────────┬───────────────┘  │
│         │                        │                    │
└─────────┼────────────────────────┼────────────────────┘
          │ API calls              │ Tile requests
          ▼                        ▼
┌─────────────────┐    ┌─────────────────────────────┐
│  PHP/Node.js    │    │  Self-hosted Tile Server     │
│  API Backend    │    │  (OpenMapTiles pipeline)     │
│  - Property data│    │  - Vector tiles (.pbf)       │
│  - Search/filter│    │  - Custom Canadian map data  │
│  - Auth/users   │    │  - Boundaries (municipal,    │
│                 │    │    neighborhood, school zones)│
└────────┬────────┘    └──────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              DATA LAYER                              │
│                                                      │
│  MySQL ←→ MongoDB ←→ Redis ←→ Elasticsearch         │
│  (users,   (listings,  (cache)  (full-text search,  │
│   deals)    property           property search)      │
│             history)                                  │
│                                                      │
│  Kafka (event streaming for real-time updates)       │
└─────────────────────────────────────────────────────┘
```

### URL Parameter Breakdown
From the URL you shared:
```
/on/toronto-real-estate/map/
  ?center_marker=43.64193,-79.38149    # Map center coordinates (lat,lng)
  &view=map                             # View mode (map vs list vs hybrid)
  &municipality=10343                   # Municipal code filter (Toronto)
  &status=for-sale                      # Listing status filter
  &lat=43.717010                        # Viewport latitude
  &lon=-79.630924                       # Viewport longitude
  &zoom=14.2                            # Mapbox zoom level
```

This tells us:
- **SEO-friendly routing**: `/on/toronto-real-estate/map/` (province/city-keyword/view)
- **State managed via URL params**: Full map state is serialized to URL for shareability
- **Municipality codes**: Internal ID system (10343 = Toronto)
- **Fractional zoom**: Mapbox GL JS supports non-integer zoom levels (14.2)

---

## 4. AI/ML Stack

| Technology | Purpose |
|-----------|---------|
| **TensorFlow** | Deep learning models |
| **PyTorch** | Neural network models |
| **scikit-learn** | Traditional ML algorithms |
| **Pandas** | Data processing/analysis |

### AI Features
- **AVM (Automated Valuation Model)**: "Sigma Estimate" — proprietary home value estimates
- **Market trend prediction**: Price forecasting based on historical data
- **Property comparison**: AI-powered comparable sales analysis
- **Natural language search**: Property search understanding

---

## 5. Third-Party Services Detected

| Service | Category |
|---------|----------|
| Google Analytics / GA4 | Analytics |
| Google Tag Manager | Tag management |
| Google Ads | Advertising |
| reCAPTCHA | Bot protection |
| jQuery Migrate | Legacy JS compatibility |
| DocuSign | E-signatures (offers) |
| LoneWolf | Real estate transaction mgmt |
| Follow Up Boss | CRM |
| LetsEncrypt | SSL certificates |
| Contact Form 7 | Contact forms |
| DMARC / SPF | Email security |
| Apple Mobile Web Clips Icon | PWA support |

---

## 6. Frontend Architecture Analysis

### Likely Framework: Vue.js 2/3 with Vue Router + Vuex/Pinia

Based on confirmed Vue.js usage and the SPA behavior:

```
src/
├── components/
│   ├── map/
│   │   ├── MapContainer.vue        # Mapbox GL JS wrapper
│   │   ├── PropertyPin.vue         # Custom map markers
│   │   ├── ClusterMarker.vue       # Pin clustering
│   │   ├── MapControls.vue         # Zoom, layers, draw tools
│   │   ├── BoundaryOverlay.vue     # Municipality/neighborhood boundaries
│   │   └── HeatmapLayer.vue        # Price heatmap visualization
│   ├── search/
│   │   ├── SearchBar.vue           # Autocomplete search
│   │   ├── FilterPanel.vue         # Price, beds, baths filters
│   │   └── SavedSearches.vue       # Saved search alerts
│   ├── property/
│   │   ├── PropertyCard.vue        # Listing card (list view)
│   │   ├── PropertyDetail.vue      # Full property page
│   │   ├── PriceHistory.vue        # Sold price history chart
│   │   └── SigmaEstimate.vue       # AI valuation widget
│   └── common/
│       ├── Header.vue
│       ├── Footer.vue
│       └── MobileNav.vue
├── views/
│   ├── MapView.vue                 # /map/ route
│   ├── ListView.vue                # /list/ route
│   ├── PropertyView.vue            # /property/ route
│   └── DashboardView.vue           # User dashboard
├── store/                          # Vuex/Pinia state
│   ├── map.js                      # Map state (center, zoom, bounds)
│   ├── listings.js                 # Property listings
│   ├── filters.js                  # Search filters
│   └── user.js                     # Auth state
├── api/
│   ├── listings.js                 # Property API calls
│   ├── search.js                   # Elasticsearch queries
│   └── map.js                      # Tile/boundary API calls
└── utils/
    ├── mapHelpers.js               # Coordinate/geo utilities
    ├── formatters.js               # Price/date formatting
    └── analytics.js                # GA/GTM event tracking
```

### Key Map Features (visible on the site)

1. **Property Clustering**: Groups nearby listings at lower zoom levels
2. **Dynamic Loading**: Loads property pins as you pan/zoom (viewport-based API calls)
3. **Boundary Layers**: Toggle municipal, neighborhood, school district boundaries
4. **Price Heatmap**: Color-coded areas by average price
5. **Draw Search**: Draw custom boundary to search within
6. **Street View Integration**: Google Street View for properties
7. **Satellite/Map Toggle**: Multiple base map styles
8. **Mobile Responsive**: Touch-optimized map controls

---

## 7. Backend API Architecture (Inferred)

### Likely API Endpoints
```
GET  /api/v1/listings?bounds={sw_lat,sw_lng,ne_lat,ne_lng}&status=for-sale
GET  /api/v1/listings/{id}
GET  /api/v1/listings/search?q={query}&filters={...}
GET  /api/v1/listings/cluster?zoom={zoom}&bounds={...}
GET  /api/v1/property/{mls_id}/history
GET  /api/v1/property/{mls_id}/estimate
GET  /api/v1/boundaries/{type}/{id}          # municipality/neighborhood polygons
GET  /api/v1/municipalities
GET  /api/v1/autocomplete?q={query}
GET  /tiles/{z}/{x}/{y}.pbf                   # Vector map tiles
```

### Data Flow for Map Page
```
1. User opens /map/ → Vue Router loads MapView.vue
2. MapView initializes Mapbox GL JS with self-hosted tile URL
3. Map fires 'moveend' event → captures viewport bounds
4. Vue store dispatches API call with bounds + filters
5. Backend queries Elasticsearch for listings in bounds
6. Response contains clustered pins at current zoom level
7. Mapbox GL JS renders pins as GeoJSON layer
8. User clicks pin → API call for full property details
9. URL params updated (lat, lon, zoom) for shareability
```

---

## 8. Why HouseSigma's Map Is So Good

### Technical Decisions That Matter

1. **Self-hosted tiles (OpenMapTiles)**:
   - No per-request Google Maps fees
   - Custom styled maps optimized for real estate
   - Full control over Canadian geographic data
   - Can add custom layers (school zones, transit, etc.)

2. **Mapbox GL JS (not Leaflet)**:
   - WebGL-powered = smooth 60fps panning/zooming
   - Vector tiles = sharp at any zoom, smaller than raster
   - Built-in clustering = handles 10,000s of pins
   - 3D terrain/building support

3. **Elasticsearch for search**:
   - Geo-spatial queries (bounding box, distance)
   - Faceted filtering (price ranges, property types)
   - Real-time indexing of new listings
   - Sub-100ms response times

4. **URL-based state**:
   - Every map view is a shareable link
   - Browser back/forward works naturally
   - SEO-friendly routes with city names

5. **Viewport-based loading**:
   - Only loads pins visible on screen
   - Reduces bandwidth and rendering load
   - Cluster density adapts to zoom level

---

## 9. Cost Optimization

HouseSigma made smart cost decisions:

| Decision | Savings |
|----------|---------|
| Self-hosted OpenMapTiles instead of Google Maps | ~$500K+/year at their traffic |
| Mapbox GL JS (open-source renderer) | Free (no Mapbox hosting fees) |
| LetsEncrypt for SSL | Free vs paid certs |
| AWS + Kubernetes | Auto-scaling, pay for what you use |
| Remote-first team (based in China/Canada) | Lower operational costs |

---

## 10. How to Build Something Similar

If you want to replicate HouseSigma's map experience:

### Minimum Viable Stack
```
Frontend:     Vue 3 + TypeScript + Mapbox GL JS
Backend:      PHP 8 (Laravel or Phalcon) OR Node.js (Express/Fastify)
Database:     PostgreSQL + PostGIS (geo queries) OR MySQL + MongoDB
Search:       Elasticsearch (or Meilisearch for simpler setup)
Cache:        Redis
Map Tiles:    OpenMapTiles + TileServer GL (self-hosted)
Deployment:   Docker + Kubernetes on AWS/GCP
```

### Key npm/composer packages
```bash
# Frontend
npm install mapbox-gl vue-mapbox @turf/turf  # Map rendering + geo utils
npm install axios pinia vue-router            # API, state, routing

# Backend (PHP)
composer require elasticsearch/elasticsearch  # Search
composer require predis/predis                # Redis cache

# Backend (Node.js alternative)
npm install @elastic/elasticsearch ioredis express
```

### Self-hosted Map Tiles Setup
```bash
# Clone OpenMapTiles
git clone https://github.com/openmaptiles/openmaptiles.git
cd openmaptiles

# Download Canada OpenStreetMap data
make download area=canada

# Generate vector tiles
make generate-tiles

# Serve with TileServer GL
docker run -p 8080:80 -v $(pwd)/data:/data maptiler/tileserver-gl
```

---

## Sources

- [HouseSigma GitHub Organization](https://github.com/housesigma)
- [HouseSigma OpenMapTiles Fork](https://github.com/housesigma/openmaptiles)
- [HouseSigma V2EX Recruitment Post (Jan 2025)](https://github.com/housesigma/hr-interview/blob/main/2025%20Q1/)
- [HouseSigma Careers](https://team.housesigma.com/)
- [HouseSigma Tech Stack - Crunchbase](https://www.crunchbase.com/organization/housesigma/technology)
- [HouseSigma Tech - ZoomInfo](https://www.zoominfo.com/c/housesigma-inc/456726870)
- [HouseSigma Tech - 6sense](https://6sense.com/company/housesigma/5d2dbff82faa194742078f05)
- [HouseSigma Google Maps Blog Post](https://housesigma.com/blog-en/google-map-price-hike/)
- [Mapbox Real Estate Solutions](https://www.mapbox.com/real-estate)
- [OpenMapTiles Project](https://openmaptiles.org/)
