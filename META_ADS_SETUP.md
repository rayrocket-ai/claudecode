# Meta Ads API — one-time setup

This connects Ray Homes' own Facebook ad account to the campaign engine so
ADMAX can create and manage Facebook + Instagram campaigns in code. You do
this once. After that, launching a campaign is one command and the daily
loop reads live numbers on its own.

Everything the engine creates is PAUSED until explicitly activated, so
nothing spends by accident during setup.

## What you need to collect (5 values)

Put these in `/opt/realtor-bot/.env` on the server:

| .env key | What it is | Where to get it |
|---|---|---|
| `META_AD_ACCOUNT_ID` | Your ad account, like `act_1234567890` | business.facebook.com → Business Settings → Accounts → Ad accounts. Prefix the number with `act_`. |
| `META_PAGE_ID` | Your Ray Homes Facebook Page id | Your Page → About → Page transparency, or Business Settings → Accounts → Pages. |
| `META_INSTAGRAM_ID` | (optional) IG account id for IG placements | Business Settings → Accounts → Instagram accounts. Leave blank to run Facebook-only at first. |
| `META_ACCESS_TOKEN` | System User token with `ads_management` | Steps below. |
| `META_API_VERSION` | Leave as `v21.0` | — |

## Getting the access token (the one real step)

1. Go to **business.facebook.com → Business Settings → Users → System Users**.
2. **Add** a system user (name it "ADMAX"), role **Admin**.
3. **Assign assets**: give this system user **Full control** of your Ray
   Homes **Page** and your **Ad account**.
4. Click **Generate new token**. Pick your Meta app (if you have none,
   create one at developers.facebook.com → Create App → type "Business").
5. Select these permissions: **`ads_management`**, **`leads_retrieval`**,
   **`pages_manage_ads`**, **`pages_read_engagement`**,
   **`business_management`**.
6. Copy the token. For a long-lived system-user token, generate it with
   "Never expires" if offered. Paste it as `META_ACCESS_TOKEN`.
7. In Ads Manager, accept the **Lead Ads Terms of Service** once (Business
   Settings → Lead access, or the first time you open a lead form). Meta
   blocks lead-form creation until this is accepted.

Note on review: managing YOUR OWN ad account and Page with a system-user
token works without full App Review. App Review / business verification is
only needed if you later manage other people's accounts.

## Verify it works

On the server:

```bash
cd /opt/realtor-bot && git pull
docker compose run --rm bot python -m integrations.meta_ads_cli verify
```

You should see your ad account name, status, and currency. If a credential
is missing it tells you exactly which one.

## Launch a campaign (per property)

1. Edit `campaigns/34-buttonleaf/meta.json`:
   - set `form.privacy_url` to your real privacy policy URL (required),
   - set `creative.image_paths` to 5 listing photos on the server,
   - confirm `creative.link` (your listing/site URL).
2. Build it (creates everything PAUSED — no spend):
   ```bash
   docker compose run --rm bot python -m integrations.meta_ads_cli build campaigns/34-buttonleaf/meta.json
   ```
3. Review in Ads Manager, then activate (this starts the $10/day):
   ```bash
   docker compose run --rm bot python -m integrations.meta_ads_cli activate campaigns/34-buttonleaf/meta.json
   ```
4. Pause anytime:
   ```bash
   docker compose run --rm bot python -m integrations.meta_ads_cli pause campaigns/34-buttonleaf/meta.json
   ```

Repeat for `campaigns/16-curry/meta.json`.

## After launch

The daily loop runs `insights` on each live campaign, writes the numbers to
the dashboard, applies the kill rules, and reports to you. You approve
activations and budget changes; the engine does the rest.

## Google Ads

Google Ads uses a separate API with a developer token that Google must
approve (a few days). That track is scaffolded separately; Meta above gets
Facebook + Instagram live now without waiting on Google.
