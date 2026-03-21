# Realty Platform — HouseSigma-Style Real Estate Search

A full-stack real estate platform with interactive map search, TRREB MLS data integration,
user accounts, saved searches, and sold price history.

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + Mapbox GL JS + Tailwind CSS
- **Backend**: PHP 8.2 / Laravel 11 + Sanctum Auth
- **Database**: MySQL 8 + Redis + Elasticsearch
- **Maps**: Self-hosted OpenMapTiles + Mapbox GL JS renderer
- **Data**: TRREB MLS feed via REALM SSO (Keycloak OIDC)
- **Deployment**: Docker Compose

## Quick Start

```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Edit backend/.env with your credentials:
#    - REALM_USERNAME / REALM_PASSWORD (TRREB SSO)
#    - MLS_API_KEY / MLS_API_SECRET
#    - MAPBOX_ACCESS_TOKEN

# 3. Start all services
docker compose up -d

# 4. Run migrations
docker compose exec api php artisan migrate

# 5. Sync MLS data
docker compose exec api php artisan trreb:sync

# 6. Open http://localhost:3000
```

## Getting TRREB API Access

1. **Register with TRREB** as a member brokerage at [trreb.ca](https://trreb.ca)
2. **Apply for IDX/VOW data feed** through the TRREB Technology department
3. **Receive RETS/RESO Web API credentials** after board approval (2-4 weeks)
4. **Configure REALM SSO** — your existing REALM credentials work for both
   TransactionDesk and the data feed

### Data Feed Options

| Feed Type | Description | Access Level |
|-----------|-------------|-------------|
| **IDX** | Active listings for public display | Member brokerages |
| **VOW** | Active + sold data for logged-in consumers | Requires user auth |
| **RETS** | Full data feed (legacy protocol) | Member brokerages |
| **RESO Web API** | Modern REST API (replacing RETS) | Member brokerages |

### Key Endpoints (once you have credentials)

```
Auth:     POST https://identity.trreb.ca/auth/realms/TRREB/protocol/openid-connect/token
Listings: GET  https://data.trreb.ca/api/v1/listings
Photos:   GET  https://data.trreb.ca/api/v1/photos/{listing_key}/{photo_num}
```

## Project Structure

```
web/
├── backend/                    # Laravel 11 API
│   ├── app/
│   │   ├── Http/Controllers/  # API controllers
│   │   ├── Models/            # Eloquent models
│   │   └── Services/          # TRREB integration, search
│   ├── database/migrations/   # MySQL schema
│   ├── routes/api.php         # API routes
│   └── config/services.php    # TRREB config
├── frontend/                   # Vue 3 SPA
│   ├── src/
│   │   ├── components/        # Vue components
│   │   │   ├── map/          # Mapbox GL map
│   │   │   ├── property/     # Property cards/details
│   │   │   ├── search/       # Search bar, filters
│   │   │   └── layout/       # Header, nav
│   │   ├── views/            # Route views
│   │   ├── store/            # Pinia state management
│   │   ├── api/              # Axios API client
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Formatters, helpers
│   └── index.html
├── docker-compose.yml          # Full stack orchestration
└── README.md
```

## API Endpoints

### Public (no auth)
- `GET /api/map/listings` — Property pins for map viewport
- `GET /api/map/clusters` — Clustered pins at low zoom
- `GET /api/search` — Search with filters
- `GET /api/autocomplete?q=` — Address/city autocomplete
- `GET /api/properties/{id}` — Full property details
- `GET /api/properties/{id}/history` — Price history
- `GET /api/properties/{id}/similar` — Similar listings
- `GET /api/stats/market-trends` — Market statistics

### Authenticated (Sanctum token)
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Sign in
- `GET /api/favorites` — Saved properties
- `POST /api/favorites/{id}` — Save property
- `GET /api/saved-searches` — Saved searches
- `POST /api/saved-searches` — Save search with alerts
- `GET /api/alerts` — New listing notifications

## Self-Hosted Map Tiles

Download and generate tiles for Canada:

```bash
git clone https://github.com/openmaptiles/openmaptiles.git
cd openmaptiles
make download area=canada
make generate-tiles
# Copy output .mbtiles to storage/tiles/
```
