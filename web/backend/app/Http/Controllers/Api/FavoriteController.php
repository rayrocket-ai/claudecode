<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Favorite;
use App\Models\Property;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class FavoriteController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $favorites = Favorite::with('property')
            ->where('user_id', $request->user()->id)
            ->orderByDesc('created_at')
            ->paginate(20);

        return response()->json($favorites);
    }

    public function store(Request $request, int $propertyId): JsonResponse
    {
        Property::findOrFail($propertyId);

        $favorite = Favorite::firstOrCreate([
            'user_id' => $request->user()->id,
            'property_id' => $propertyId,
        ]);

        return response()->json(['data' => $favorite], 201);
    }

    public function destroy(Request $request, int $propertyId): JsonResponse
    {
        Favorite::where('user_id', $request->user()->id)
            ->where('property_id', $propertyId)
            ->delete();

        return response()->json(null, 204);
    }
}
