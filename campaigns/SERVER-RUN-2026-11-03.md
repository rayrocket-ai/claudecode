# Finish the Nov 3 ad work from the server (about 10 minutes, once)

The server talks to Facebook directly, so there is no Ad Advisor action
limit and no expiring link. Nothing here turns an ad on. Everything new is
created PAUSED; Ray activates after looking at the previews.

## 1. Let the server read the creative (2 clicks)

In Google Drive, set these two folders to **Anyone with the link: Viewer**
(right-click, Share, General access):

- the 53 Alpha cuts folder (holds `53-alpha-A-tour-15s-9x16.mp4` and
  `53-alpha-C-tour-25s-9x16.mp4`)
- `85Sidney-478676-images-mls-202609261438-new`

## 2. Make the server's Facebook key (5 minutes)

business.facebook.com > Business Settings > Users > **System users** >
Add "ADMAX" (Admin). Then **Assign assets**, Full control, on all of:

- Ad account **732663023528570** (runs 34 Buttonleaf and 16 Curry)
- Ad account **1788128334781323** (the new Alpha, Sidney, Jackman campaigns)
- Page **Ray Homes Team** and Instagram **rayahmadi**

Click **Generate new token**, tick `ads_management`, `pages_manage_ads`,
`pages_read_engagement`, `leads_retrieval`, `business_management`, choose
**Never expire**, copy it.

## 3. Put it on the server and run (paste as one block)

```bash
cd /opt/realtor-bot && git pull
cat >> .env <<'ENV'
META_ACCESS_TOKEN=PASTE_THE_TOKEN_HERE
META_AD_ACCOUNT_ID=act_1788128334781323
META_PAGE_ID=1033110506750808
META_INSTAGRAM_ID=17841401464994148
ENV
nano .env   # replace PASTE_THE_TOKEN_HERE with the real token, save
docker compose run --rm bot python -m integrations.meta_ads_cli verify
docker compose run --rm bot python -m integrations.meta_ads_cli run-ops campaigns/OPS-2026-11-03.json
```

## What run-ops does (campaigns/OPS-2026-11-03.json)

1. Pauses **16 Curry** (sold).
2. Lowers **34 Buttonleaf** to $5/day.
3. Replaces Buttonleaf's ad copy with a no-address version (same video,
   same lead form).
4. **53 Alpha**: adds the $5/day ad set (Vaughan, 25 km) and two video ads.
5. **85 Sidney**: adds the $5/day ad set (Bowmanville, 25 km) and a
   5-photo carousel ad.
6. **97 Jackman**: adds the $5/day ad set only. It still needs a video.

Each step is recorded in `campaigns/OPS-2026-11-03.state.json`. If one
fails, fix the cause and run the same command again; finished steps are
skipped. Then send ADMAX the output.
