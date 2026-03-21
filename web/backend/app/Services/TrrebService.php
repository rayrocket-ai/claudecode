<?php

namespace App\Services;

use App\Models\Property;
use App\Models\PriceHistory;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

/**
 * TRREB (Toronto Regional Real Estate Board) Data Integration Service.
 *
 * Handles authentication via REALM SSO (Keycloak) and data retrieval
 * from TRREB's MLS data feed. Supports both RETS and RESO Web API.
 *
 * To get API access:
 * 1. Register as a TRREB member brokerage
 * 2. Apply for IDX/VOW data feed access at trreb.ca
 * 3. Receive RETS/RESO credentials after board approval
 * 4. Configure REALM SSO for TransactionDesk/IDX access
 */
class TrrebService
{
    private string $realmAuthUrl;
    private string $clientId;
    private string $username;
    private string $password;
    private string $feedUrl;
    private string $apiKey;
    private string $apiSecret;

    public function __construct()
    {
        $this->realmAuthUrl = config('services.trreb.realm_auth_url');
        $this->clientId = config('services.trreb.realm_client_id');
        $this->username = config('services.trreb.realm_username');
        $this->password = config('services.trreb.realm_password');
        $this->feedUrl = config('services.trreb.feed_url');
        $this->apiKey = config('services.trreb.api_key');
        $this->apiSecret = config('services.trreb.api_secret');
    }

    /**
     * Authenticate with TRREB REALM SSO (Keycloak OIDC).
     * Returns a bearer token for subsequent API calls.
     */
    public function authenticate(): string
    {
        $cacheKey = 'trreb_access_token';

        return Cache::remember($cacheKey, 3500, function () {
            $tokenUrl = "{$this->realmAuthUrl}/protocol/openid-connect/token";

            $response = Http::asForm()->post($tokenUrl, [
                'grant_type' => 'password',
                'client_id' => $this->clientId,
                'username' => $this->username,
                'password' => $this->password,
            ]);

            if (!$response->successful()) {
                Log::error('TRREB REALM auth failed', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);
                throw new \RuntimeException('Failed to authenticate with TRREB REALM SSO');
            }

            return $response->json('access_token');
        });
    }

    /**
     * Fetch active listings from TRREB MLS data feed.
     * Supports incremental updates via timestamp parameter.
     */
    public function fetchActiveListings(?string $since = null, int $limit = 500, int $offset = 0): array
    {
        $token = $this->authenticate();

        $params = [
            'status' => 'A', // Active
            'limit' => $limit,
            'offset' => $offset,
        ];

        if ($since) {
            $params['modified_since'] = $since;
        }

        $response = Http::withToken($token)
            ->withHeaders([
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->get("{$this->feedUrl}/listings", $params);

        if (!$response->successful()) {
            Log::error('TRREB listing fetch failed', [
                'status' => $response->status(),
                'params' => $params,
            ]);
            throw new \RuntimeException('Failed to fetch TRREB listings');
        }

        return $response->json();
    }

    /**
     * Fetch sold/historical data from TRREB.
     */
    public function fetchSoldListings(?string $since = null, int $limit = 500, int $offset = 0): array
    {
        $token = $this->authenticate();

        $params = [
            'status' => 'S', // Sold
            'limit' => $limit,
            'offset' => $offset,
        ];

        if ($since) {
            $params['sold_since'] = $since;
        }

        $response = Http::withToken($token)
            ->withHeaders([
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->get("{$this->feedUrl}/listings", $params);

        if (!$response->successful()) {
            Log::error('TRREB sold data fetch failed', ['status' => $response->status()]);
            throw new \RuntimeException('Failed to fetch TRREB sold data');
        }

        return $response->json();
    }

    /**
     * Fetch a single listing by MLS number.
     */
    public function fetchListing(string $mlsNumber): ?array
    {
        $token = $this->authenticate();

        $response = Http::withToken($token)
            ->withHeaders([
                'X-API-Key' => $this->apiKey,
                'Accept' => 'application/json',
            ])
            ->get("{$this->feedUrl}/listings/{$mlsNumber}");

        if ($response->status() === 404) {
            return null;
        }

        if (!$response->successful()) {
            throw new \RuntimeException("Failed to fetch listing {$mlsNumber}");
        }

        return $response->json();
    }

    /**
     * Sync listings from TRREB feed into local database.
     * This is the main ETL pipeline.
     */
    public function syncListings(string $type = 'active', ?string $since = null): int
    {
        $offset = 0;
        $limit = 500;
        $totalSynced = 0;

        do {
            $data = $type === 'active'
                ? $this->fetchActiveListings($since, $limit, $offset)
                : $this->fetchSoldListings($since, $limit, $offset);

            $listings = $data['results'] ?? $data['data'] ?? [];

            if (empty($listings)) break;

            foreach ($listings as $listing) {
                $this->upsertProperty($listing);
                $totalSynced++;
            }

            $offset += $limit;

            Log::info("TRREB sync progress", [
                'type' => $type,
                'synced' => $totalSynced,
                'batch_size' => count($listings),
            ]);

        } while (count($listings) === $limit);

        Log::info("TRREB sync complete", ['type' => $type, 'total' => $totalSynced]);

        return $totalSynced;
    }

    /**
     * Map TRREB/RETS field names to our database schema and upsert.
     */
    private function upsertProperty(array $data): Property
    {
        $mapped = $this->mapFields($data);

        $property = Property::updateOrCreate(
            ['mls_number' => $mapped['mls_number']],
            $mapped
        );

        // Track price history
        $this->recordPriceHistory($property, $data);

        return $property;
    }

    /**
     * Map TRREB/RETS data fields to our Property model fields.
     * TRREB uses RETS standard field names.
     */
    private function mapFields(array $data): array
    {
        // RETS field mapping - adjust based on your actual TRREB feed schema
        return [
            'mls_number' => $data['ListingKey'] ?? $data['MlsNumber'] ?? $data['ml_num'],
            'status' => $this->mapStatus($data['StandardStatus'] ?? $data['Status'] ?? ''),
            'property_type' => $this->mapPropertyType($data['PropertyType'] ?? $data['Type_Own1_Out'] ?? ''),

            // Location
            'street_number' => $data['StreetNumber'] ?? $data['Addr'] ?? '',
            'street_name' => $data['StreetName'] ?? $data['St'] ?? '',
            'unit_number' => $data['UnitNumber'] ?? $data['Apt_Unit'] ?? null,
            'city' => $data['City'] ?? $data['Municipality'] ?? '',
            'province' => $data['StateOrProvince'] ?? 'ON',
            'postal_code' => $data['PostalCode'] ?? $data['Zip'] ?? '',
            'neighborhood' => $data['SubdivisionName'] ?? $data['Community'] ?? null,
            'municipality' => $data['Municipality'] ?? $data['Area'] ?? null,
            'municipality_code' => $data['MunicipalityCode'] ?? $data['Municipality_Code'] ?? null,
            'community' => $data['CommunityName'] ?? $data['Community'] ?? null,

            // Geo
            'latitude' => (float) ($data['Latitude'] ?? $data['Lat'] ?? 0),
            'longitude' => (float) ($data['Longitude'] ?? $data['Lng'] ?? 0),

            // Pricing
            'list_price' => (int) ($data['ListPrice'] ?? $data['Lp_Dol'] ?? 0),
            'sold_price' => !empty($data['ClosePrice'] ?? $data['Sp_Dol'] ?? null)
                ? (int) ($data['ClosePrice'] ?? $data['Sp_Dol'])
                : null,
            'original_price' => !empty($data['OriginalListPrice'] ?? $data['Orig_Dol'] ?? null)
                ? (int) ($data['OriginalListPrice'] ?? $data['Orig_Dol'])
                : null,

            // Details
            'bedrooms' => (int) ($data['BedroomsTotal'] ?? $data['Br'] ?? 0),
            'bedrooms_plus' => (int) ($data['BedroomsAboveGrade'] ?? $data['Br_Plus'] ?? 0),
            'bathrooms' => (int) ($data['BathroomsTotalInteger'] ?? $data['Bath_Tot'] ?? 0),
            'washrooms' => (int) ($data['BathroomsFull'] ?? $data['Wash_Tot'] ?? 0),
            'parking_spaces' => (int) ($data['ParkingTotal'] ?? $data['Park_Spcs'] ?? 0),
            'garage_type' => $data['GarageType'] ?? $data['Gar_Type'] ?? null,
            'interior_sqft' => !empty($data['LivingArea']) ? (int) $data['LivingArea'] : null,
            'sqft_range' => $data['LivingAreaRange'] ?? $data['Sqft'] ?? null,
            'lot_size_sqft' => !empty($data['LotSizeArea']) ? (int) $data['LotSizeArea'] : null,
            'lot_size_frontage' => $data['LotSizeFrontage'] ?? $data['Front_Ft'] ?? null,
            'lot_size_depth' => $data['LotSizeDepth'] ?? $data['Depth'] ?? null,
            'year_built' => !empty($data['YearBuilt'] ?? $data['Yr_Built'] ?? null)
                ? (int) ($data['YearBuilt'] ?? $data['Yr_Built'])
                : null,
            'stories' => !empty($data['StoriesTotal']) ? (int) $data['StoriesTotal'] : null,

            // Features
            'basement' => $data['Basement'] ?? $data['Bsmt1_Out'] ?? null,
            'heating' => $data['Heating'] ?? $data['Heat_Inc'] ?? null,
            'cooling' => $data['Cooling'] ?? $data['A_C'] ?? null,
            'exterior' => $data['ExteriorFeatures'] ?? $data['Ext1_Out'] ?? null,
            'pool' => $data['PoolFeatures'] ?? $data['Pool'] ?? null,
            'style' => $data['ArchitecturalStyle'] ?? $data['Style'] ?? null,
            'description' => $data['PublicRemarks'] ?? $data['Ad_Text'] ?? null,

            // Condo
            'maintenance_fee' => !empty($data['AssociationFee'] ?? $data['Maint'] ?? null)
                ? (float) ($data['AssociationFee'] ?? $data['Maint'])
                : null,
            'condo_exposure' => $data['Exposure'] ?? null,

            // Tax
            'annual_taxes' => !empty($data['TaxAnnualAmount'] ?? $data['Taxes'] ?? null)
                ? (int) ($data['TaxAnnualAmount'] ?? $data['Taxes'])
                : null,
            'tax_year' => !empty($data['TaxYear']) ? (int) $data['TaxYear'] : null,

            // Dates
            'list_date' => $data['ListingContractDate'] ?? $data['Input_Date'] ?? null,
            'sold_date' => $data['CloseDate'] ?? $data['Cd'] ?? null,
            'days_on_market' => !empty($data['DaysOnMarket'] ?? $data['Dom'] ?? null)
                ? (int) ($data['DaysOnMarket'] ?? $data['Dom'])
                : null,

            // Agent
            'listing_agent_name' => $data['ListAgentFullName'] ?? $data['Rltr'] ?? null,
            'listing_brokerage' => $data['ListOfficeName'] ?? $data['Office'] ?? null,

            // Media
            'photos' => $this->extractPhotos($data),
            'virtual_tour_url' => $data['VirtualTourURLUnbranded'] ?? $data['Tour_Url'] ?? null,

            // Legal
            'legal_description' => $data['LegalDescription'] ?? $data['Legal'] ?? null,
            'zoning' => $data['Zoning'] ?? null,

            // Raw
            'raw_data' => $data,
            'data_updated_at' => now(),
        ];
    }

    private function mapStatus(string $status): string
    {
        return match (strtoupper($status)) {
            'A', 'ACTIVE', 'NEW' => 'for-sale',
            'S', 'SOLD', 'CLOSED' => 'sold',
            'T', 'TERMINATED', 'CANCELLED', 'EXPIRED' => 'terminated',
            'U', 'SUSPENDED' => 'suspended',
            'L', 'LEASED' => 'leased',
            default => 'for-sale',
        };
    }

    private function mapPropertyType(string $type): string
    {
        $normalized = strtolower(trim($type));
        return match (true) {
            str_contains($normalized, 'detach') && !str_contains($normalized, 'semi') => 'detached',
            str_contains($normalized, 'semi') => 'semi-detached',
            str_contains($normalized, 'town') && str_contains($normalized, 'condo') => 'condo-townhouse',
            str_contains($normalized, 'town') || str_contains($normalized, 'row') => 'townhouse',
            str_contains($normalized, 'condo') || str_contains($normalized, 'apt') => 'condo-apt',
            str_contains($normalized, 'duplex') => 'duplex',
            str_contains($normalized, 'triplex') => 'triplex',
            str_contains($normalized, 'multi') => 'multiplex',
            str_contains($normalized, 'vacant') || str_contains($normalized, 'land') => 'vacant-land',
            str_contains($normalized, 'farm') => 'farm',
            str_contains($normalized, 'comm') => 'commercial',
            default => 'other',
        };
    }

    private function extractPhotos(array $data): array
    {
        // RETS photo extraction - format varies by board
        if (!empty($data['Media'])) {
            return collect($data['Media'])
                ->where('MediaCategory', 'Photo')
                ->pluck('MediaURL')
                ->toArray();
        }

        if (!empty($data['PhotoUrls'])) {
            return $data['PhotoUrls'];
        }

        // Build URLs from photo count
        if (!empty($data['PhotosCount']) && !empty($data['ListingKey'])) {
            $photos = [];
            for ($i = 1; $i <= min((int) $data['PhotosCount'], 30); $i++) {
                $photos[] = "{$this->feedUrl}/photos/{$data['ListingKey']}/{$i}";
            }
            return $photos;
        }

        return [];
    }

    private function recordPriceHistory(Property $property, array $data): void
    {
        $existingLatest = PriceHistory::where('property_id', $property->id)
            ->orderByDesc('event_date')
            ->first();

        $currentPrice = $property->sold_price ?? $property->list_price;
        $status = $property->status;

        // Determine event type
        $eventType = match ($status) {
            'sold' => 'sold',
            'terminated' => 'terminated',
            'suspended' => 'suspended',
            default => $existingLatest ? 'price-change' : 'listed',
        };

        // Skip if price hasn't changed and not a status change
        if ($existingLatest
            && $existingLatest->price === $currentPrice
            && $eventType === 'price-change') {
            return;
        }

        PriceHistory::create([
            'property_id' => $property->id,
            'mls_number' => $property->mls_number,
            'event_type' => $eventType,
            'price' => $currentPrice,
            'previous_price' => $existingLatest?->price,
            'event_date' => $property->sold_date ?? $property->list_date ?? now()->toDateString(),
            'source' => 'trreb',
        ]);
    }
}
