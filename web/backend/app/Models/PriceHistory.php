<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class PriceHistory extends Model
{
    protected $table = 'price_history';

    protected $fillable = [
        'property_id', 'mls_number', 'event_type',
        'price', 'previous_price', 'event_date', 'source',
    ];

    protected function casts(): array
    {
        return [
            'price' => 'integer',
            'previous_price' => 'integer',
            'event_date' => 'date',
        ];
    }

    public function property(): BelongsTo
    {
        return $this->belongsTo(Property::class);
    }

    public function getPriceChangeAttribute(): ?int
    {
        if (!$this->previous_price) return null;
        return $this->price - $this->previous_price;
    }

    public function getPriceChangePercentAttribute(): ?float
    {
        if (!$this->previous_price) return null;
        return round(($this->price - $this->previous_price) / $this->previous_price * 100, 1);
    }
}
