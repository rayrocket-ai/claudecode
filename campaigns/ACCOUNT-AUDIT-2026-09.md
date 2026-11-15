# Ad Account Audit — Sep 17, 2026

Scope: what can be established about Ray's Google Ads and Meta ad accounts
from account emails (billing, lead notifications, policy notices) plus
Drive. No direct Ads Manager access existed at audit time, so campaign
structure, keywords, impressions, CTR and per-campaign spend are NOT
visible here — those need an Ads Manager export or API access.

---

## 1. Google Ads — Customer ID 134-435-0136 ("Ray Ahmadi Real Estate")

Payer disclosure: "Ads funded by Rahmatullah Ahmadi Professional Real
Estate Corporation." Payments profile 8008-5021-2266. A second Google Ads
customer ID also appears in API notices: 156-142-2047 (likely a second
account or manager account; check which is live).

### 1a. HEADLINE: the account is spending real money on out-of-market junk leads

"You have a new lead through your Google ad" notifications, Jun 22 – Aug 18
2026 (~20 leads). Lead source, per the email itself: the Google **Business
Profile "contact us" form** ("optimized for your ad") — not a qualified
lead form.

| Date (UTC) | Name | Phone | Origin |
|---|---|---|---|
| Aug 18 | Nida Macabudbod | +63 915… | Philippines |
| Aug 17 | Ken Mason | 949 833… | USA (Orange County, CA) |
| Aug 16 | achilles dela cruz | +63 917… | Philippines |
| Aug 10 | vincent mativo | +63 948… | Philippines |
| Aug 10 | Ryan Mansuganday | +63 961… | Philippines |
| Aug 9 | Ruby Among | +63 963… | Philippines |
| Aug 4 | Rey Conoman | +63 915… | Philippines |
| Aug 1 | zian brylle simbajon | not provided | (Filipino name) |
| Jul 30 | Banban Pogi | +63 963… | Philippines ("Pogi" = slang, fake) |
| Jul 29 | AJOHN RAFAEL CAMACHO | not provided | (Filipino name, all caps) |
| Jul 28 | Marie Dante | +63 970… | Philippines |
| Jul 20 | Jeriko jablan | +63 926… | Philippines |
| Jul 20 | Nasser Saligan | 0952 609… | Philippines (mobile format) |
| Jul 19 | 5 leads in ~10 min (05:47–05:51) + 2 at 15:34 | — | bot burst |
| Jul 18 | 2 leads | — | — |
| Jun 22 | 1 lead | — | — |

**Zero leads from Ontario or anywhere in Canada.** For a GTA brokerage, the
observed lead volume is ~100% unusable. The Jul 19 burst (5 submissions in
minutes) is a bot signature.

Most likely causes (all fixable in Ads Manager in minutes):
1. Location option left on the default **"Presence or interest"**, which
   serves ads to people merely "interested in" Toronto from anywhere.
2. Wide or wrong location targets, no country exclusions.
3. The Business Profile contact form as the lead destination — a known
   spam magnet with no qualifying friction.

### 1b. Spend (payments received)
- Jul 22, 2020: CA$500.00
- May 31, 2021: CA$722.25
- Jan 21, 2026: CA$362.13
- Aug 1, 2026: CA$231.46 (after a same-day decline on MC •3175)
Run-rate while active in 2026: roughly CA$230–360/month.

### 1c. Chronic billing instability (this alone wrecks performance)
Declined payments across 10 different cards, 2019–2026: Visa •5557
(expired 2019), •4850, •5306, •0332, •6484 ("bank reported account
closed" 2020, 2023), •7641 (expired 2024); Mastercard •2432, •8962, •3175;
Amex •1011.

Service SUSPENDED for non-payment: Oct 2024 ($400.50), May 2025 ($522.30),
Oct 2025 ($333.43), Nov 2025 ($38.32), Dec 2025 – Jan 21 2026 ("URGENT
suspended", underpayment). Jan 7 2026: "Your ad may not be running."

Effect: campaigns stop and restart unpredictably, smart bidding never
accumulates stable conversion data, and every restart re-enters learning.
Even perfect targeting cannot perform on this billing pattern.

### 1d. Account hygiene signals (neglected / autopilot)
- Conversion actions were not on data-driven attribution (forced upgrade
  notice Mar 2026) → conversion tracking was set up long ago and untouched.
- Call-only ads deprecation notice (Jan 2026) → legacy call-only ads existed.
- Video Action campaigns auto-upgraded to Demand Gen (2025) → legacy video
  campaigns existed; whatever they became is unmanaged.
- Quarterly Security Suggestions unaddressed (Dec 2024, Mar 2025, Sep 2025).
- EU political ads confirmation requested (Sep 2025), unclear if done.
- Conversion-based customer lists auto-enrolled (Jun/Jul 2026).
- Google Ads API MFA notice (May 2026) → some API access/developer setup
  already exists on 156-142-2047. Worth locating; it may shortcut the
  Google integration.

---

## 2. Meta (Facebook / Instagram)

### 2a. Ray's own ad account is dormant
Last "Your ad is approved" for account "Ray Ahmadi": **Mar 11, 2017**
(campaign "Vaughan"; boosted posts Nov–Dec 2016 before that). No Meta ad
receipts, performance emails or lead notifications since. The account has
effectively not run ads for ~9.5 years. This is why nothing ADMAX planned
could go live: there was no active Meta ad infrastructure to plug into.

### 2b. Business Manager access is tangled
In 2020 Ray was granted access to OTHER businesses' Facebook assets: The
A+ Team / A+ Team Group (Andy Zheng), Gurpreet Gill, Sasi Subramaniam.
When generating the ADMAX system-user token, make sure it is created in
RAY HOMES' own Business Manager, not one of these.

### 2c. Security churn on the Facebook login (flag, not alarm)
Password changed Aug 13, Aug 18, Aug 21 and Sep 7, 2026; login-with-code
Aug 11 and Sep 8 (Sep 8 from Vaughan, ON); passkey created Sep 8. Pattern
is consistent with Ray repeatedly locked out and resetting. If any of
those were NOT Ray, secure the account immediately. If they were, the
Sep 8 passkey should stop the churn — a stable login is a prerequisite for
generating the ads token.

---

## 3. What this means

- The only ad money moving today is Google, and on the evidence it is
  buying Philippine spam form-fills at CA$230–360/month while the account
  cycles through suspensions. Caveat: lead emails are the only performance
  signal visible here; if the campaign also drives calls or site visits,
  those are not captured in this audit.
- Meta is a clean slate. Nothing to fix, everything to build.

## 4. Prioritized actions

P0 — today, ~5 minutes in Google Ads (stops the bleeding):
1. Campaign → Settings → Locations → "Location options" → select
   **Presence: People in or regularly in your targeted locations.**
2. Location targets: GTA municipalities only (Vaughan, Richmond Hill,
   Markham, Stouffville, Aurora, Georgetown/Halton Hills, Mississauga,
   Brampton, Ajax, Barrie or as intended). Add **Philippines** and
   **United States** as excluded locations.
3. Disable the Business Profile "contact us" form as the lead path (link is
   in every lead email), OR replace with a Search lead-form asset that has
   qualifying questions.
4. Billing: one reliable card + a backup payment method, so the account
   stops suspending. Clear any balance.

P1 — this week:
5. Export from Google Ads: Campaigns (last 90 days), Search terms, and
   "User locations" report → share the CSVs → full performance analysis.
6. Inventory campaign types: kill leftover call-only remnants, review the
   auto-upgraded Demand Gen campaign(s), confirm what is actually running.
7. Conversion tracking: confirm what counts as a conversion; add call and
   lead-form conversions if missing so bidding optimizes toward real leads.
8. Identify what 156-142-2047 is and whether its API access can be reused.

P2 — rebuild:
9. Google: consolidate to the ADMAX Search plan (buyer / seller / valuation
   intent, Presence-only targeting, tight negatives, AI Max expansions OFF
   until tested).
10. Meta: treat as new. Stabilize the Facebook login, generate the
    system-user token in Ray Homes' Business Manager per META_ADS_SETUP.md,
    then build with the ADMAX 2026 structure (one campaign, one ad set,
    10–15 creatives, higher-intent form).

---

## CORRECTION — Sep 17, 2026 (after the Ad Advisor connector came online)

Section 2a above was wrong. The email-only audit concluded Ray's Meta ad
account was dormant since 2017 because Meta stopped sending "ad approved"
emails. Ad Advisor shows two Meta ad accounts, both named "Ray Ahmadi":

- **732663023528570** — ACTIVE. Ray's working account. Both ADMAX
  campaigns are live here: 34 Buttonleaf (sprint Jul 20–27, relaunched
  Aug 11) and 16 Curry (Aug 11). Through the Aug 20 snapshot: $243.41
  spend, 21 leads, blended CPL $11.59. Page 1033110506750808, pixel
  1793927534188323, IG 17841401464994148. Also holds 2024 Marketplace
  rental boosts and 2025 Instagram post boosts.
- **1788128334781323** — IDLE since ~Feb 2026. 168 campaigns, 2023–2026,
  agency-style naming (pre-construction condo lead gen: UnionCity, Burnet,
  Kipling Station, The Clove, Oakville Yards; listing lead gen; retargeting).
  Nearly all $5/day ABO — the starved-test anti-pattern. Nothing spending.

Both accounts were authorized against an older Ad Advisor app version, so
the connector is a frozen snapshot (as of Aug 20 / Apr 26) until Ray
reconnects Meta at app.adadvisor.ai/settings/integrations. No writes are
possible until then. Lead-form reads additionally require Ad Advisor's
Data Use Checkup to be complete on Meta's side.

Section 3's "Meta is a clean slate" is therefore also wrong: Meta is the
one channel that IS working. Priorities update: keep both Meta campaigns
running; expand creative to 10–15 per ad set; verify lead quality; then
scale by 20–30% steps. The Google findings in Section 1 stand unchanged
and still need the Google API path or the 5-minute manual fix — Ad
Advisor does not cover Google Ads.
