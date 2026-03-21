<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class PropertyAlert extends Model
{
    protected $fillable = [
        'user_id', 'saved_search_id', 'property_id',
        'alert_type', 'is_read', 'is_emailed',
    ];

    protected function casts(): array
    {
        return [
            'is_read' => 'boolean',
            'is_emailed' => 'boolean',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function savedSearch(): BelongsTo
    {
        return $this->belongsTo(SavedSearch::class);
    }

    public function property(): BelongsTo
    {
        return $this->belongsTo(Property::class);
    }
}
