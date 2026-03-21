<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\PropertyController;
use App\Http\Controllers\Api\MapController;
use App\Http\Controllers\Api\UserController;
use App\Http\Controllers\Api\FavoriteController;
use App\Http\Controllers\Api\SavedSearchController;
use App\Http\Controllers\Api\StatsController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Public Routes (no auth required, but rate-limited)
|--------------------------------------------------------------------------
*/

// Auth
Route::prefix('auth')->group(function () {
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login', [AuthController::class, 'login']);
    Route::post('/forgot-password', [AuthController::class, 'forgotPassword']);
    Route::post('/reset-password', [AuthController::class, 'resetPassword']);
});

// Map & Search (public, read-only)
Route::prefix('map')->group(function () {
    Route::get('/listings', [MapController::class, 'listings']);
    Route::get('/clusters', [MapController::class, 'clusters']);
    Route::get('/boundaries/{type}', [MapController::class, 'boundaries']);
});

Route::get('/search', [PropertyController::class, 'search']);
Route::get('/autocomplete', [PropertyController::class, 'autocomplete']);

// Property details (public)
Route::prefix('properties')->group(function () {
    Route::get('/{id}', [PropertyController::class, 'show']);
    Route::get('/{id}/history', [PropertyController::class, 'priceHistory']);
    Route::get('/{id}/similar', [PropertyController::class, 'similar']);
    Route::get('/mls/{mlsNumber}', [PropertyController::class, 'showByMls']);
});

// Neighborhood stats (public)
Route::prefix('stats')->group(function () {
    Route::get('/neighborhoods/{city}', [StatsController::class, 'neighborhoodList']);
    Route::get('/neighborhood/{name}', [StatsController::class, 'neighborhoodDetail']);
    Route::get('/market-trends', [StatsController::class, 'marketTrends']);
});

/*
|--------------------------------------------------------------------------
| Protected Routes (require Sanctum auth)
|--------------------------------------------------------------------------
*/

Route::middleware('auth:sanctum')->group(function () {
    // User profile
    Route::get('/user', [UserController::class, 'profile']);
    Route::put('/user', [UserController::class, 'updateProfile']);
    Route::put('/user/password', [UserController::class, 'updatePassword']);
    Route::post('/auth/logout', [AuthController::class, 'logout']);

    // Favorites
    Route::prefix('favorites')->group(function () {
        Route::get('/', [FavoriteController::class, 'index']);
        Route::post('/{propertyId}', [FavoriteController::class, 'store']);
        Route::delete('/{propertyId}', [FavoriteController::class, 'destroy']);
    });

    // Saved Searches
    Route::prefix('saved-searches')->group(function () {
        Route::get('/', [SavedSearchController::class, 'index']);
        Route::post('/', [SavedSearchController::class, 'store']);
        Route::put('/{id}', [SavedSearchController::class, 'update']);
        Route::delete('/{id}', [SavedSearchController::class, 'destroy']);
    });

    // Recently Viewed
    Route::get('/recently-viewed', [UserController::class, 'recentlyViewed']);

    // Alerts
    Route::prefix('alerts')->group(function () {
        Route::get('/', [UserController::class, 'alerts']);
        Route::put('/{id}/read', [UserController::class, 'markAlertRead']);
        Route::put('/read-all', [UserController::class, 'markAllAlertsRead']);
    });
});
