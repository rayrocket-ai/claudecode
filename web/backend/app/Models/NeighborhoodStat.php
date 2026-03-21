<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class NeighborhoodStat extends Model
{
    protected $table = 'neighborhood_stats';

    protected $fillable = [
        'neighborhood', 'city', 'municipality_code', 'property_type', 'period',
        'total_listings', 'total_sold',
        'avg_sold_price', 'median_sold_price', 'avg_list_price',
        'avg_sold_to_list_ratio', 'avg_days_on_market', 'avg_price_per_sqft',
    ];

    protected function casts(): array
    {
        return [
            'avg_sold_to_list_ratio' => 'float',
            'avg_price_per_sqft' => 'float',
        ];
    }
}
