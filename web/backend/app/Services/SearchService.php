<?php

namespace App\Services;

use App\Models\Property;
use Illuminate\Support\Facades\DB;

/**
 * Property search service with geo-spatial queries.
 * Uses MySQL for basic queries, can be extended to Elasticsearch for full-text.
 */
class SearchService
{
    /**
     * Search properties within map viewport bounds with filters.
     */
    public function searchInBounds(array $params): array
    {
        $query = Property::query();

        // Viewport bounds (required for map view)
        if (!empty($params['bounds'])) {
            $b = $params['bounds'];
            $query->inBounds($b['sw_lat'], $b['sw_lng'], $b['ne_lat'], $b['ne_lng']);
        }

        // Status filter
        $status = $params['status'] ?? 'for-sale';
        if ($status === 'sold') {
            $query->sold();
            if (!empty($params['sold_within_days'])) {
                $query->where('sold_date', '>=', now()->subDays((int) $params['sold_within_days']));
            }
        } else {
            $query->forSale();
        }

        // Property type
        if (!empty($params['property_type'])) {
            $types = is_array($params['property_type']) ? $params['property_type'] : [$params['property_type']];
            $query->whereIn('property_type', $types);
        }

        // Price range
        $query->priceRange($params['price_min'] ?? null, $params['price_max'] ?? null);

        // Bedrooms / Bathrooms
        $query->bedrooms($params['beds_min'] ?? null);
        $query->bathrooms($params['baths_min'] ?? null);

        // City / Neighborhood
        if (!empty($params['city'])) {
            $query->inCity($params['city']);
        }
        if (!empty($params['neighborhood'])) {
            $query->where('neighborhood', $params['neighborhood']);
        }
        if (!empty($params['municipality_code'])) {
            $query->where('municipality_code', $params['municipality_code']);
        }

        // Year built
        if (!empty($params['year_built_min'])) {
            $query->where('year_built', '>=', (int) $params['year_built_min']);
        }

        // Sqft
        if (!empty($params['sqft_min'])) {
            $query->where('interior_sqft', '>=', (int) $params['sqft_min']);
        }

        // Keywords in description
        if (!empty($params['keywords'])) {
            $query->where('description', 'LIKE', "%{$params['keywords']}%");
        }

        // Sort
        $sortBy = $params['sort_by'] ?? 'list_date';
        $sortDir = $params['sort_dir'] ?? 'desc';
        $query->orderBy($sortBy, $sortDir);

        // Pagination
        $limit = min((int) ($params['limit'] ?? 100), 500);
        $page = (int) ($params['page'] ?? 1);

        return [
            'data' => $query->paginate($limit, ['*'], 'page', $page),
            'total' => $query->count(),
        ];
    }

    /**
     * Get clustered pins for map display at lower zoom levels.
     * Groups nearby properties into clusters with count and average price.
     */
    public function getClusters(array $params): array
    {
        $bounds = $params['bounds'];
        $zoom = (int) ($params['zoom'] ?? 12);

        // Grid size depends on zoom level
        $gridSize = $this->getGridSize($zoom);

        $status = $params['status'] ?? 'for-sale';

        $query = DB::table('properties')
            ->whereNull('deleted_at')
            ->where('status', $status === 'sold' ? 'sold' : 'for-sale')
            ->whereBetween('latitude', [$bounds['sw_lat'], $bounds['ne_lat']])
            ->whereBetween('longitude', [$bounds['sw_lng'], $bounds['ne_lng']]);

        // Apply filters
        if (!empty($params['property_type'])) {
            $types = is_array($params['property_type']) ? $params['property_type'] : [$params['property_type']];
            $query->whereIn('property_type', $types);
        }
        if (!empty($params['price_min'])) $query->where('list_price', '>=', (int) $params['price_min']);
        if (!empty($params['price_max'])) $query->where('list_price', '<=', (int) $params['price_max']);
        if (!empty($params['beds_min'])) $query->where('bedrooms', '>=', (int) $params['beds_min']);

        $clusters = $query->select(
            DB::raw("ROUND(latitude / {$gridSize}) * {$gridSize} as cluster_lat"),
            DB::raw("ROUND(longitude / {$gridSize}) * {$gridSize} as cluster_lng"),
            DB::raw('COUNT(*) as count'),
            DB::raw('AVG(list_price) as avg_price'),
            DB::raw('MIN(list_price) as min_price'),
            DB::raw('MAX(list_price) as max_price'),
        )
        ->groupBy('cluster_lat', 'cluster_lng')
        ->get();

        return $clusters->map(function ($cluster) {
            return [
                'lat' => (float) $cluster->cluster_lat,
                'lng' => (float) $cluster->cluster_lng,
                'count' => (int) $cluster->count,
                'avg_price' => (int) $cluster->avg_price,
                'min_price' => (int) $cluster->min_price,
                'max_price' => (int) $cluster->max_price,
            ];
        })->toArray();
    }

    /**
     * Autocomplete search for addresses, neighborhoods, cities.
     */
    public function autocomplete(string $query, int $limit = 10): array
    {
        $results = [];

        // Search cities
        $cities = Property::where('city', 'LIKE', "{$query}%")
            ->select('city', DB::raw('COUNT(*) as count'))
            ->groupBy('city')
            ->orderByDesc('count')
            ->limit(3)
            ->get()
            ->map(fn ($r) => [
                'type' => 'city',
                'label' => $r->city,
                'value' => $r->city,
                'count' => $r->count,
            ]);

        // Search neighborhoods
        $neighborhoods = Property::where('neighborhood', 'LIKE', "{$query}%")
            ->select('neighborhood', 'city', DB::raw('COUNT(*) as count'))
            ->groupBy('neighborhood', 'city')
            ->orderByDesc('count')
            ->limit(3)
            ->get()
            ->map(fn ($r) => [
                'type' => 'neighborhood',
                'label' => "{$r->neighborhood}, {$r->city}",
                'value' => $r->neighborhood,
                'city' => $r->city,
                'count' => $r->count,
            ]);

        // Search addresses
        $addresses = Property::where('status', 'for-sale')
            ->where(function ($q) use ($query) {
                $q->where('street_name', 'LIKE', "%{$query}%")
                  ->orWhere('mls_number', 'LIKE', "{$query}%");
            })
            ->select('id', 'mls_number', 'street_number', 'street_name', 'unit_number', 'city')
            ->limit(5)
            ->get()
            ->map(fn ($p) => [
                'type' => 'address',
                'label' => $p->short_address . ", {$p->city}",
                'value' => $p->mls_number,
                'id' => $p->id,
            ]);

        return $cities->merge($neighborhoods)->merge($addresses)->take($limit)->values()->toArray();
    }

    private function getGridSize(int $zoom): float
    {
        // Smaller grid = more clusters at lower zoom, individual pins at higher zoom
        return match (true) {
            $zoom >= 16 => 0.0005,  // Individual pins
            $zoom >= 14 => 0.002,
            $zoom >= 12 => 0.005,
            $zoom >= 10 => 0.02,
            $zoom >= 8 => 0.05,
            default => 0.1,
        };
    }
}
