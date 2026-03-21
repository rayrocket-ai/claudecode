<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\SavedSearch;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class SavedSearchController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $searches = SavedSearch::where('user_id', $request->user()->id)
            ->orderByDesc('created_at')
            ->get();

        return response()->json(['data' => $searches]);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:100'],
            'filters' => ['required', 'array'],
            'bounds' => ['nullable', 'array'],
            'city' => ['nullable', 'string'],
            'neighborhood' => ['nullable', 'string'],
            'email_alerts' => ['nullable', 'boolean'],
            'alert_frequency' => ['nullable', 'in:instant,daily,weekly'],
        ]);

        $search = SavedSearch::create([
            'user_id' => $request->user()->id,
            ...$validated,
        ]);

        return response()->json(['data' => $search], 201);
    }

    public function update(Request $request, int $id): JsonResponse
    {
        $search = SavedSearch::where('user_id', $request->user()->id)->findOrFail($id);

        $validated = $request->validate([
            'name' => ['nullable', 'string', 'max:100'],
            'filters' => ['nullable', 'array'],
            'bounds' => ['nullable', 'array'],
            'email_alerts' => ['nullable', 'boolean'],
            'alert_frequency' => ['nullable', 'in:instant,daily,weekly'],
        ]);

        $search->update(array_filter($validated, fn ($v) => $v !== null));

        return response()->json(['data' => $search]);
    }

    public function destroy(Request $request, int $id): JsonResponse
    {
        SavedSearch::where('user_id', $request->user()->id)->findOrFail($id)->delete();

        return response()->json(null, 204);
    }
}
