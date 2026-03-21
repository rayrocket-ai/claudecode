<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;

class Property extends Model
{
    use HasFactory, SoftDeletes;

    protected $fillable = [
        'mls_number', 'status', 'property_type',
        'street_number', 'street_name', 'unit_number', 'city', 'province',
        'postal_code', 'neighborhood', 'municipality', 'municipality_code', 'community',
        'latitude', 'longitude',
        'list_price', 'sold_price', 'original_price', 'price_per_sqft',
        'bedrooms', 'bedrooms_plus', 'bathrooms', 'washrooms',
        'parking_spaces', 'garage_type',
        'lot_size_sqft', 'lot_size_frontage', 'lot_size_depth',
        'interior_sqft', 'sqft_range', 'year_built', 'stories',
        'basement', 'heating', 'cooling', 'exterior', 'pool', 'style', 'description',
        'maintenance_fee', 'condo_corp_name', 'condo_exposure', 'condo_floor', 'condo_amenities',
        'annual_taxes', 'tax_year', 'assessment_value',
        'list_date', 'sold_date', 'days_on_market', 'possession_date',
        'listing_agent_name', 'listing_brokerage', 'co_op_brokerage',
        'photos', 'virtual_tour_url',
        'legal_description', 'zoning',
        'raw_data', 'data_updated_at',
    ];

    protected function casts(): array
    {
        return [
            'latitude' => 'float',
            'longitude' => 'float',
            'list_price' => 'integer',
            'sold_price' => 'integer',
            'original_price' => 'integer',
            'price_per_sqft' => 'float',
            'maintenance_fee' => 'float',
            'photos' => 'array',
            'condo_amenities' => 'array',
            'raw_data' => 'array',
            'list_date' => 'date',
            'sold_date' => 'date',
            'possession_date' => 'date',
            'data_updated_at' => 'datetime',
        ];
    }

    public function priceHistory(): HasMany
    {
        return $this->hasMany(PriceHistory::class)->orderByDesc('event_date');
    }

    public function favorites(): HasMany
    {
        return $this->hasMany(Favorite::class);
    }

    public function getFullAddressAttribute(): string
    {
        $parts = [$this->street_number, $this->street_name];
        if ($this->unit_number) {
            array_unshift($parts, "#{$this->unit_number}");
        }
        $parts[] = $this->city;
        $parts[] = $this->province;
        $parts[] = $this->postal_code;
        return implode(' ', array_filter($parts));
    }

    public function getShortAddressAttribute(): string
    {
        $addr = "{$this->street_number} {$this->street_name}";
        if ($this->unit_number) {
            $addr = "#{$this->unit_number} - {$addr}";
        }
        return $addr;
    }

    public function getPrimaryPhotoAttribute(): ?string
    {
        return $this->photos[0] ?? null;
    }

    public function getSoldToListRatioAttribute(): ?float
    {
        if (!$this->sold_price || !$this->list_price) return null;
        return round($this->sold_price / $this->list_price * 100, 1);
    }

    public function scopeForSale($query)
    {
        return $query->where('status', 'for-sale');
    }

    public function scopeSold($query)
    {
        return $query->where('status', 'sold');
    }

    public function scopeInBounds($query, float $swLat, float $swLng, float $neLat, float $neLng)
    {
        return $query->whereBetween('latitude', [$swLat, $neLat])
                     ->whereBetween('longitude', [$swLng, $neLng]);
    }

    public function scopeInCity($query, string $city)
    {
        return $query->where('city', $city);
    }

    public function scopePriceRange($query, ?int $min, ?int $max)
    {
        if ($min) $query->where('list_price', '>=', $min);
        if ($max) $query->where('list_price', '<=', $max);
        return $query;
    }

    public function scopeBedrooms($query, ?int $min)
    {
        if ($min) $query->where('bedrooms', '>=', $min);
        return $query;
    }

    public function scopeBathrooms($query, ?int $min)
    {
        if ($min) $query->where('bathrooms', '>=', $min);
        return $query;
    }
}
