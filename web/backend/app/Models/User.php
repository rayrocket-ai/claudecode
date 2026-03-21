<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable, SoftDeletes;

    protected $fillable = [
        'name', 'email', 'password', 'phone', 'avatar_url',
        'role', 'brokerage', 'license_number', 'preferences',
    ];

    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'preferences' => 'array',
        ];
    }

    public function savedSearches(): HasMany
    {
        return $this->hasMany(SavedSearch::class);
    }

    public function favorites(): HasMany
    {
        return $this->hasMany(Favorite::class);
    }

    public function recentlyViewed(): HasMany
    {
        return $this->hasMany(RecentlyViewed::class)->orderByDesc('viewed_at');
    }

    public function alerts(): HasMany
    {
        return $this->hasMany(PropertyAlert::class)->orderByDesc('created_at');
    }

    public function isAgent(): bool
    {
        return $this->role === 'agent';
    }

    public function isAdmin(): bool
    {
        return $this->role === 'admin';
    }
}
