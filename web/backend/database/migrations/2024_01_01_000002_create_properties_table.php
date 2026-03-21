<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('properties', function (Blueprint $table) {
            $table->id();
            $table->string('mls_number', 20)->unique();
            $table->enum('status', ['for-sale', 'sold', 'terminated', 'suspended', 'leased', 'for-lease'])->index();
            $table->enum('property_type', [
                'detached', 'semi-detached', 'townhouse', 'condo-apt',
                'condo-townhouse', 'duplex', 'triplex', 'multiplex',
                'vacant-land', 'farm', 'commercial', 'other'
            ])->index();

            // Location
            $table->string('street_number', 20);
            $table->string('street_name');
            $table->string('unit_number', 20)->nullable();
            $table->string('city')->index();
            $table->string('province', 2)->default('ON');
            $table->string('postal_code', 7);
            $table->string('neighborhood')->nullable()->index();
            $table->string('municipality')->nullable()->index();
            $table->unsignedInteger('municipality_code')->nullable()->index();
            $table->string('community')->nullable();

            // Geo coordinates
            $table->decimal('latitude', 10, 7)->index();
            $table->decimal('longitude', 10, 7)->index();

            // Pricing
            $table->unsignedBigInteger('list_price');
            $table->unsignedBigInteger('sold_price')->nullable();
            $table->unsignedBigInteger('original_price')->nullable();
            $table->decimal('price_per_sqft', 10, 2)->nullable();

            // Property details
            $table->unsignedTinyInteger('bedrooms')->nullable();
            $table->unsignedTinyInteger('bedrooms_plus')->nullable();
            $table->unsignedTinyInteger('bathrooms')->nullable();
            $table->unsignedTinyInteger('washrooms')->nullable();
            $table->unsignedSmallInteger('parking_spaces')->nullable();
            $table->string('garage_type', 50)->nullable();
            $table->unsignedInteger('lot_size_sqft')->nullable();
            $table->string('lot_size_frontage', 30)->nullable();
            $table->string('lot_size_depth', 30)->nullable();
            $table->unsignedInteger('interior_sqft')->nullable();
            $table->string('sqft_range', 30)->nullable();
            $table->unsignedSmallInteger('year_built')->nullable();
            $table->unsignedTinyInteger('stories')->nullable();

            // Features
            $table->string('basement', 100)->nullable();
            $table->string('heating', 100)->nullable();
            $table->string('cooling', 100)->nullable();
            $table->string('exterior', 100)->nullable();
            $table->string('pool', 50)->nullable();
            $table->string('style', 100)->nullable();
            $table->text('description')->nullable();

            // Condo specific
            $table->decimal('maintenance_fee', 10, 2)->nullable();
            $table->string('condo_corp_name')->nullable();
            $table->string('condo_exposure', 10)->nullable();
            $table->unsignedSmallInteger('condo_floor')->nullable();
            $table->json('condo_amenities')->nullable();

            // Tax & Assessment
            $table->unsignedInteger('annual_taxes')->nullable();
            $table->unsignedSmallInteger('tax_year')->nullable();
            $table->unsignedBigInteger('assessment_value')->nullable();

            // Dates
            $table->date('list_date')->nullable()->index();
            $table->date('sold_date')->nullable()->index();
            $table->unsignedSmallInteger('days_on_market')->nullable();
            $table->date('possession_date')->nullable();

            // Agent/Brokerage
            $table->string('listing_agent_name')->nullable();
            $table->string('listing_brokerage')->nullable();
            $table->string('co_op_brokerage')->nullable();

            // Media
            $table->json('photos')->nullable();
            $table->string('virtual_tour_url')->nullable();

            // Legal
            $table->text('legal_description')->nullable();
            $table->string('zoning', 50)->nullable();

            // Metadata
            $table->json('raw_data')->nullable();
            $table->timestamp('data_updated_at')->nullable();
            $table->timestamps();
            $table->softDeletes();

            // Spatial index for geo queries
            $table->index(['latitude', 'longitude']);
            $table->index(['status', 'property_type', 'city']);
            $table->index(['status', 'list_price']);
            $table->index(['sold_date', 'city']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('properties');
    }
};
