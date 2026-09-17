# Google Ads API — one-time setup

After this, ADMAX can pull the campaign / search-term / location reports
itself, set Presence-only targeting, add country exclusions, and pause a
campaign — on Ray's own Google Ads account, no Ads Manager clicking.

Account facts already known: Customer ID **134-435-0136** ("Ray Ahmadi
Real Estate"). A second ID, **156-142-2047**, has received Google Ads API
developer emails, so some API setup may already exist — check it first,
it could save the developer-token wait.

## The 5 values for `/opt/realtor-bot/.env`

| .env key | What | Where |
|---|---|---|
| `GOOGLE_ADS_CUSTOMER_ID` | `1344350136` (digits only) | Known. |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | API access token for your account | Google Ads → a **Manager account** → Tools → **API Center**. If you have no manager account, create one at ads.google.com/home/tools/manager-accounts (free) and link 134-435-0136 under it. New tokens start as **Test access**; apply for **Basic access** in API Center (usually 1–3 business days) to read a live account. |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Manager account id (digits) | Only if the token comes from a manager account. |
| `GOOGLE_ADS_CLIENT_ID` / `GOOGLE_ADS_CLIENT_SECRET` | OAuth client | console.cloud.google.com → new project → APIs & Services → Library → enable **Google Ads API** → Credentials → Create → **OAuth client ID** → type **Desktop app**. Copy id + secret. On the OAuth consent screen add your Gmail as a test user. |
| `GOOGLE_ADS_REFRESH_TOKEN` | Long-lived login | Minted by the `auth` command below, once. |

## Mint the refresh token (one time, ~2 minutes)

On the server, after the client id/secret are in `.env`:

```bash
cd /opt/realtor-bot && git pull
docker compose run --rm -p 8765:8765 bot python -m integrations.google_ads_cli auth
```

It prints a Google URL. Open it in a browser signed in to
**r4166252070@gmail.com** (the account that owns the Ads account), approve,
and the command prints `GOOGLE_ADS_REFRESH_TOKEN=...`. Paste that into
`.env`. (If the browser cannot reach localhost on the server, run the same
command on a laptop with Python: `pip install httpx pydantic-settings`,
then `python -m integrations.google_ads_cli auth` from a repo checkout.)

## Verify

```bash
docker compose run --rm bot python -m integrations.google_ads_cli verify
```

Shows the account name, currency and time zone. Missing values are named.

## Then the engine does the work

```bash
# The three reports Ray was asked to export, plus the presence-vs-interest
# leak summary (how much spend went to people NOT in the GTA):
docker compose run --rm bot python -m integrations.google_ads_cli export --days 90

# Stop the Philippine-spam leak on a campaign (Presence-only + exclusions):
docker compose run --rm bot python -m integrations.google_ads_cli fix-geo <campaign_id> --exclude PH,US

# Pause a campaign outright:
docker compose run --rm bot python -m integrations.google_ads_cli pause <campaign_id>
```

Campaign ids come from the `export` output.

## Safety

- Reports are read-only.
- `fix-geo` and `pause` are the only account changes and are run
  deliberately by command; nothing runs on a schedule until Ray approves.
- The refresh token can be revoked any time at myaccount.google.com →
  Security → Third-party access.
