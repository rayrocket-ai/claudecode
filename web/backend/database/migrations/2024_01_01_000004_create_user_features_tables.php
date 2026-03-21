<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('saved_searches', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->json('filters');       // {status, property_type, price_min, price_max, beds, baths, ...}
            $table->json('bounds')->nullable(); // {sw_lat, sw_lng, ne_lat, ne_lng}
            $table->string('city')->nullable();
            $table->string('neighborhood')->nullable();
            $table->boolean('email_alerts')->default(true);
            $table->enum('alert_frequency', ['instant', 'daily', 'weekly'])->default('daily');
            $table->timestamp('last_alerted_at')->nullable();
            $table->timestamps();

            $table->index(['user_id', 'email_alerts']);
        });

        Schema::create('favorites', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->foreignId('property_id')->constrained()->cascadeOnDelete();
            $table->text('notes')->nullable();
            $table->timestamps();

            $table->unique(['user_id', 'property_id']);
        });

        Schema::create('recently_viewed', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->foreignId('property_id')->constrained()->cascadeOnDelete();
            $table->timestamp('viewed_at');

            $table->index(['user_id', 'viewed_at']);
            $table->unique(['user_id', 'property_id']);
        });

        Schema::create('property_alerts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->foreignId('saved_search_id')->constrained()->cascadeOnDelete();
            $table->foreignId('property_id')->constrained()->cascadeOnDelete();
            $table->enum('alert_type', ['new-listing', 'price-change', 'sold', 'back-on-market']);
            $table->boolean('is_read')->default(false);
            $table->boolean('is_emailed')->default(false);
            $table->timestamps();

            $table->index(['user_id', 'is_read', 'created_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('property_alerts');
        Schema::dropIfExists('recently_viewed');
        Schema::dropIfExists('favorites');
        Schema::dropIfExists('saved_searches');
    }
};
