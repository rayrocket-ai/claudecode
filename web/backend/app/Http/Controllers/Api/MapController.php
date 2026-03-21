<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\SearchService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class MapController extends Controller
{
    public function __construct(
        private SearchService $searchService
    ) {}

    /**
     * GET /api/map/listings
     * Returns property pins for the current map viewport.
     */
    public function listings(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'sw_lat' => ['required', 'numeric'],
            'sw_lng' => ['required', 'numeric'],
            'ne_lat' => ['required', 'numeric'],
            'ne_lng' => ['required', 'numeric'],
            'zoom' => ['nullable', 'numeric'],
            'status' => ['nullable', 'in:for-sale,sold'],
            'property_type' => ['nullable', 'string'],
            'price_min' => ['nullable', 'integer', 'min:0'],
            'price_max' => ['nullable', 'integer', 'min:0'],
            'beds_min' => ['nullable', 'integer', 'min:0'],
            'baths_min' => ['nullable', 'integer', 'min:0'],
            'sold_within_days' => ['nullable', 'integer', 'in:30,90,180,365'],
            'limit' => ['nullable', 'integer', 'max:500'],
            'page' => ['nullable', 'integer', 'min:1'],
        ]);

        $zoom = (float) ($validated['zoom'] ?? 12);

        $params = [
            'bounds' => [
                'sw_lat' => (float) $validated['sw_lat'],
                'sw_lng' => (float) $validated['sw_lng'],
                'ne_lat' => (float) $validated['ne_lat'],
                'ne_lng' => (float) $validated['ne_lng'],
            ],
            'status' => $validated['status'] ?? 'for-sale',
            'property_type' => !empty($validated['property_type'])
                ? explode(',', $validated['property_type'])
                : null,
            'price_min' => $validated['price_min'] ?? null,
            'price_max' => $validated['price_max'] ?? null,
            'beds_min' => $validated['beds_min'] ?? null,
            'baths_min' => $validated['baths_min'] ?? null,
            'sold_within_days' => $validated['sold_within_days'] ?? null,
            'limit' => $validated['limit'] ?? 200,
            'page' => $validated['page'] ?? 1,
        ];

        // Use clusters at low zoom, individual pins at high zoom
        if ($zoom < 14) {
            $clusters = $this->searchService->getClusters(array_merge($params, ['zoom' => (int) $zoom]));
            return response()->json([
                'type' => 'clusters',
                'data' => $clusters,
            ]);
        }

        $result = $this->searchService->searchInBounds($params);
        $listings = $result['data'];

        // Return GeoJSON for map rendering
        $features = $listings->getCollection()->map(function ($property) {
            return [
                'type' => 'Feature',
                'geometry' => [
                    'type' => 'Point',
                    'coordinates' => [$property->longitude, $property->latitude],
                ],
                'properties' => [
                    'id' => $property->id,
                    'mls' => $property->mls_number,
                    'price' => $property->status === 'sold' ? $property->sold_price : $property->list_price,
                    'beds' => $property->bedrooms,
                    'baths' => $property->bathrooms,
                    'type' => $property->property_type,
                    'status' => $property->status,
                    'address' => $property->short_address,
                    'photo' => $property->primary_photo,
                    'sqft' => $property->sqft_range ?? $property->interior_sqft,
                    'days_on_market' => $property->days_on_market,
                ],
            ];
        });

        return response()->json([
            'type' => 'geojson',
            'data' => [
                'type' => 'FeatureCollection',
                'features' => $features->values(),
            ],
            'pagination' => [
                'current_page' => $listings->currentPage(),
                'total' => $listings->total(),
                'per_page' => $listings->perPage(),
                'last_page' => $listings->lastPage(),
            ],
        ]);
    }

    /**
     * GET /api/map/clusters
     * Returns clustered pins for overview zoom levels.
     */
    public function clusters(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'sw_lat' => ['required', 'numeric'],
            'sw_lng' => ['required', 'numeric'],
            'ne_lat' => ['required', 'numeric'],
            'ne_lng' => ['required', 'numeric'],
            'zoom' => ['required', 'integer'],
            'status' => ['nullable', 'in:for-sale,sold'],
            'property_type' => ['nullable', 'string'],
            'price_min' => ['nullable', 'integer'],
            'price_max' => ['nullable', 'integer'],
            'beds_min' => ['nullable', 'integer'],
        ]);

        $params = [
            'bounds' => [
                'sw_lat' => (float) $validated['sw_lat'],
                'sw_lng' => (float) $validated['sw_lng'],
                'ne_lat' => (float) $validated['ne_lat'],
                'ne_lng' => (float) $validated['ne_lng'],
            ],
            'zoom' => (int) $validated['zoom'],
            'status' => $validated['status'] ?? 'for-sale',
            'property_type' => !empty($validated['property_type'])
                ? explode(',', $validated['property_type'])
                : null,
            'price_min' => $validated['price_min'] ?? null,
            'price_max' => $validated['price_max'] ?? null,
            'beds_min' => $validated['beds_min'] ?? null,
        ];

        $clusters = $this->searchService->getClusters($params);

        return response()->json(['data' => $clusters]);
    }

    /**
     * GET /api/map/boundaries/{type}
     * Returns GeoJSON boundaries for municipalities, neighborhoods, etc.
     */
    public function boundaries(Request $request, string $type): JsonResponse
    {
        $validTypes = ['municipality', 'neighborhood', 'school-district'];
        if (!in_array($type, $validTypes)) {
            return response()->json(['error' => 'Invalid boundary type'], 400);
        }

        // Boundaries are stored as GeoJSON files in storage
        $path = storage_path("app/boundaries/{$type}.geojson");

        if (!file_exists($path)) {
            return response()->json(['error' => 'Boundary data not found'], 404);
        }

        $geojson = json_decode(file_get_contents($path), true);

        return response()->json($geojson);
    }
}
