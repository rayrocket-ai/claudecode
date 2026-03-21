<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\NeighborhoodStat;
use App\Models\Property;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class StatsController extends Controller
{
    /**
     * GET /api/stats/neighborhoods/{city}
     */
    public function neighborhoodList(string $city): JsonResponse
    {
        $neighborhoods = NeighborhoodStat::where('city', $city)
            ->where('period', now()->format('Y-m'))
            ->select('neighborhood', 'property_type', 'avg_sold_price', 'total_sold', 'avg_days_on_market')
            ->orderBy('neighborhood')
            ->get()
            ->groupBy('neighborhood');

        return response()->json(['data' => $neighborhoods]);
    }

    /**
     * GET /api/stats/neighborhood/{name}
     */
    public function neighborhoodDetail(Request $request, string $name): JsonResponse
    {
        $city = $request->query('city', 'Toronto');
        $months = (int) $request->query('months', 12);

        $stats = NeighborhoodStat::where('neighborhood', $name)
            ->where('city', $city)
            ->where('period', '>=', now()->subMonths($months)->format('Y-m'))
            ->orderBy('period')
            ->get();

        // Current active listings count
        $activeCount = Property::forSale()
            ->where('neighborhood', $name)
            ->where('city', $city)
            ->count();

        return response()->json([
            'neighborhood' => $name,
            'city' => $city,
            'active_listings' => $activeCount,
            'trends' => $stats,
        ]);
    }

    /**
     * GET /api/stats/market-trends
     */
    public function marketTrends(Request $request): JsonResponse
    {
        $city = $request->query('city', 'Toronto');
        $months = (int) $request->query('months', 12);
        $propertyType = $request->query('property_type');

        $query = NeighborhoodStat::where('city', $city)
            ->where('period', '>=', now()->subMonths($months)->format('Y-m'));

        if ($propertyType) {
            $query->where('property_type', $propertyType);
        }

        // Aggregate across all neighborhoods per month
        $trends = $query->select(
            'period',
            DB::raw('SUM(total_listings) as total_listings'),
            DB::raw('SUM(total_sold) as total_sold'),
            DB::raw('AVG(avg_sold_price) as avg_sold_price'),
            DB::raw('AVG(median_sold_price) as median_sold_price'),
            DB::raw('AVG(avg_sold_to_list_ratio) as avg_sold_to_list_ratio'),
            DB::raw('AVG(avg_days_on_market) as avg_days_on_market'),
            DB::raw('AVG(avg_price_per_sqft) as avg_price_per_sqft'),
        )
        ->groupBy('period')
        ->orderBy('period')
        ->get();

        return response()->json(['data' => $trends]);
    }
}
