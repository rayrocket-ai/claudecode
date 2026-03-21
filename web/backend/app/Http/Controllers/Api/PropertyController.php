<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Property;
use App\Models\RecentlyViewed;
use App\Services\SearchService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class PropertyController extends Controller
{
    public function __construct(
        private SearchService $searchService
    ) {}

    /**
     * GET /api/search
     */
    public function search(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'q' => ['nullable', 'string', 'max:255'],
            'status' => ['nullable', 'in:for-sale,sold'],
            'property_type' => ['nullable', 'string'],
            'price_min' => ['nullable', 'integer', 'min:0'],
            'price_max' => ['nullable', 'integer', 'min:0'],
            'beds_min' => ['nullable', 'integer', 'min:0'],
            'baths_min' => ['nullable', 'integer', 'min:0'],
            'city' => ['nullable', 'string'],
            'neighborhood' => ['nullable', 'string'],
            'municipality_code' => ['nullable', 'integer'],
            'sort_by' => ['nullable', 'in:list_price,list_date,sold_date,bedrooms,days_on_market'],
            'sort_dir' => ['nullable', 'in:asc,desc'],
            'limit' => ['nullable', 'integer', 'max:100'],
            'page' => ['nullable', 'integer', 'min:1'],
        ]);

        $params = array_filter($validated, fn ($v) => $v !== null);
        if (!empty($params['property_type'])) {
            $params['property_type'] = explode(',', $params['property_type']);
        }

        $result = $this->searchService->searchInBounds($params);

        return response()->json($result['data']);
    }

    /**
     * GET /api/autocomplete
     */
    public function autocomplete(Request $request): JsonResponse
    {
        $query = $request->validate(['q' => ['required', 'string', 'min:2', 'max:100']])['q'];
        $results = $this->searchService->autocomplete($query);

        return response()->json(['data' => $results]);
    }

    /**
     * GET /api/properties/{id}
     */
    public function show(Request $request, int $id): JsonResponse
    {
        $property = Property::with('priceHistory')->findOrFail($id);

        // Track view if authenticated
        if ($user = $request->user()) {
            RecentlyViewed::updateOrCreate(
                ['user_id' => $user->id, 'property_id' => $id],
                ['viewed_at' => now()]
            );
        }

        $data = $property->toArray();
        $data['full_address'] = $property->full_address;
        $data['short_address'] = $property->short_address;
        $data['sold_to_list_ratio'] = $property->sold_to_list_ratio;
        $data['is_favorited'] = $request->user()
            ? $property->favorites()->where('user_id', $request->user()->id)->exists()
            : false;

        return response()->json(['data' => $data]);
    }

    /**
     * GET /api/properties/mls/{mlsNumber}
     */
    public function showByMls(Request $request, string $mlsNumber): JsonResponse
    {
        $property = Property::with('priceHistory')
            ->where('mls_number', $mlsNumber)
            ->firstOrFail();

        return $this->show($request, $property->id);
    }

    /**
     * GET /api/properties/{id}/history
     */
    public function priceHistory(int $id): JsonResponse
    {
        $property = Property::findOrFail($id);
        $history = $property->priceHistory()->get();

        // Also find all historical listings at same address
        $addressHistory = Property::where('street_number', $property->street_number)
            ->where('street_name', $property->street_name)
            ->where('city', $property->city)
            ->where('unit_number', $property->unit_number)
            ->where('id', '!=', $property->id)
            ->withTrashed()
            ->with('priceHistory')
            ->get();

        return response()->json([
            'current' => $history,
            'address_history' => $addressHistory,
        ]);
    }

    /**
     * GET /api/properties/{id}/similar
     */
    public function similar(int $id): JsonResponse
    {
        $property = Property::findOrFail($id);

        // Find similar properties: same type, nearby, similar price
        $similar = Property::forSale()
            ->where('id', '!=', $id)
            ->where('property_type', $property->property_type)
            ->where('city', $property->city)
            ->whereBetween('list_price', [
                (int) ($property->list_price * 0.8),
                (int) ($property->list_price * 1.2),
            ])
            ->orderByRaw('ABS(latitude - ?) + ABS(longitude - ?)', [$property->latitude, $property->longitude])
            ->limit(12)
            ->get()
            ->map(fn ($p) => [
                'id' => $p->id,
                'mls_number' => $p->mls_number,
                'address' => $p->short_address,
                'city' => $p->city,
                'price' => $p->list_price,
                'beds' => $p->bedrooms,
                'baths' => $p->bathrooms,
                'sqft' => $p->sqft_range ?? $p->interior_sqft,
                'photo' => $p->primary_photo,
                'property_type' => $p->property_type,
                'days_on_market' => $p->days_on_market,
            ]);

        return response()->json(['data' => $similar]);
    }
}
