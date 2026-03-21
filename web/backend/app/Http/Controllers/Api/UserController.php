<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\PropertyAlert;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules;

class UserController extends Controller
{
    public function profile(Request $request): JsonResponse
    {
        $user = $request->user();
        return response()->json([
            'data' => $user->only('id', 'name', 'email', 'phone', 'avatar_url', 'role', 'preferences'),
        ]);
    }

    public function updateProfile(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => ['nullable', 'string', 'max:255'],
            'phone' => ['nullable', 'string', 'max:20'],
            'preferences' => ['nullable', 'array'],
        ]);

        $request->user()->update(array_filter($validated, fn ($v) => $v !== null));

        return response()->json(['data' => $request->user()->fresh()]);
    }

    public function updatePassword(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'current_password' => ['required'],
            'password' => ['required', 'confirmed', Rules\Password::defaults()],
        ]);

        if (!Hash::check($validated['current_password'], $request->user()->password)) {
            return response()->json(['message' => 'Current password is incorrect'], 422);
        }

        $request->user()->update(['password' => Hash::make($validated['password'])]);

        return response()->json(['message' => 'Password updated']);
    }

    public function recentlyViewed(Request $request): JsonResponse
    {
        $viewed = $request->user()->recentlyViewed()
            ->with('property')
            ->limit(50)
            ->get();

        return response()->json(['data' => $viewed]);
    }

    public function alerts(Request $request): JsonResponse
    {
        $alerts = $request->user()->alerts()
            ->with(['property', 'savedSearch'])
            ->paginate(20);

        return response()->json($alerts);
    }

    public function markAlertRead(Request $request, int $id): JsonResponse
    {
        PropertyAlert::where('user_id', $request->user()->id)
            ->findOrFail($id)
            ->update(['is_read' => true]);

        return response()->json(['message' => 'Marked as read']);
    }

    public function markAllAlertsRead(Request $request): JsonResponse
    {
        PropertyAlert::where('user_id', $request->user()->id)
            ->where('is_read', false)
            ->update(['is_read' => true]);

        return response()->json(['message' => 'All marked as read']);
    }
}
