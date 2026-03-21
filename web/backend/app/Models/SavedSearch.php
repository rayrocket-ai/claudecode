<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class SavedSearch extends Model
{
    protected $fillable = [
        'user_id', 'name', 'filters', 'bounds',
        'city', 'neighborhood',
        'email_alerts', 'alert_frequency', 'last_alerted_at',
    ];

    protected function casts(): array
    {
        return [
            'filters' => 'array',
            'bounds' => 'array',
            'email_alerts' => 'boolean',
            'last_alerted_at' => 'datetime',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function alerts(): HasMany
    {
        return $this->hasMany(PropertyAlert::class);
    }
}
