<?php

return [
    'trreb' => [
        'realm_auth_url' => env('REALM_AUTH_URL', 'https://identity.trreb.ca/auth/realms/TRREB'),
        'realm_client_id' => env('REALM_CLIENT_ID'),
        'realm_username' => env('REALM_USERNAME'),
        'realm_password' => env('REALM_PASSWORD'),
        'feed_url' => env('MLS_FEED_URL', 'https://data.trreb.ca/api/v1'),
        'api_key' => env('MLS_API_KEY'),
        'api_secret' => env('MLS_API_SECRET'),
    ],

    'mapbox' => [
        'access_token' => env('MAPBOX_ACCESS_TOKEN'),
    ],

    'tiles' => [
        'server_url' => env('TILE_SERVER_URL', 'http://localhost:8080'),
    ],
];
