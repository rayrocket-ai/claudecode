<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('price_history', function (Blueprint $table) {
            $table->id();
            $table->foreignId('property_id')->constrained()->cascadeOnDelete();
            $table->string('mls_number', 20)->index();
            $table->enum('event_type', ['listed', 'price-change', 'sold', 'terminated', 'suspended', 're-listed']);
            $table->unsignedBigInteger('price');
            $table->unsignedBigInteger('previous_price')->nullable();
            $table->date('event_date');
            $table->string('source', 50)->nullable();
            $table->timestamps();

            $table->index(['mls_number', 'event_date']);
            $table->index(['property_id', 'event_date']);
        });

        Schema::create('neighborhood_stats', function (Blueprint $table) {
            $table->id();
            $table->string('neighborhood')->index();
            $table->string('city')->index();
            $table->unsignedInteger('municipality_code')->nullable();
            $table->string('property_type', 50)->index();
            $table->char('period', 7)->index(); // YYYY-MM format
            $table->unsignedInteger('total_listings')->default(0);
            $table->unsignedInteger('total_sold')->default(0);
            $table->unsignedBigInteger('avg_sold_price')->nullable();
            $table->unsignedBigInteger('median_sold_price')->nullable();
            $table->unsignedBigInteger('avg_list_price')->nullable();
            $table->decimal('avg_sold_to_list_ratio', 5, 3)->nullable();
            $table->unsignedSmallInteger('avg_days_on_market')->nullable();
            $table->decimal('avg_price_per_sqft', 10, 2)->nullable();
            $table->timestamps();

            $table->unique(['neighborhood', 'city', 'property_type', 'period']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('neighborhood_stats');
        Schema::dropIfExists('price_history');
    }
};
