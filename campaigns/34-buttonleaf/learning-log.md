# 34 Buttonleaf — Learning Log

Every test gets: hypothesis, variants, spend, result, decision, lesson.
Newest entries at the top. Never re-test a settled question without new
justification.

---
## 2026-11-12 — Relist is live. First YouTube numbers

- Relist live on REALTOR.ca Nov 11, 4:35 PM: MLS N14172060, $1,299,000,
  4+1 bed, 5 bath. SkySlope offer link issued the same day.
  realtor.ca/real-estate/30504118/34-buttonleaf-crescent-whitchurch-stouffville-stouffville
- YouTube (Google Ads 24114799139), resumed Nov 10. Through Nov 11: $9.40
  spent, about 16 clicks, CTR 1.19%, about $0.59 a click, 0 tracked
  conversions. Nearly all of it on Nov 11 (about $9.20, Google is allowed to
  run up to twice the daily budget on one day and averages it out).
- Hypothesis "database-only audience is too small to spend $5/day": refuted.
  It spent the full budget and more on day one.
- Problem: those clicks went to the OLD listing page (lid 29957682). The
  relist has a new MLS number, so that page is probably dead or stale.
  Proposed fix for Ray: point the ad at the new listing page on
  rayahmadi.com (need the link) or at rayahmadi.com/contact like the Alpha ad.
- Kill rules: not applicable yet, two days of data. First real read Nov 16.
- Meta: no Facebook security or verification email since Nov 9, so the hold
  is assumed still on. Did not retry the lead-form build: the Nov 11
  unattended run stalled on an approval prompt for that write and never
  reported. Writes now wait until Ray is in the chat.
- Pabbly: no new alert for the Buttonleaf workflow. Still paused as far as
  the inbox shows. A separate alert today is for the Google Review workflow.
- Adspirer quota: 9 of 15 used after today's pull.

---
## 2026-11-10 (night) — YouTube resumed on Ray's word. Website settled

- Ray: "you take over and get this done". Resumed Google Ads campaign
  24114799139 ("Video ad - 34 Buttonleaf Cres", Demand Gen, $5/day). Status
  PAUSED to ENABLED. Copy has no price or address.
- Known weak points to fix next: audience is the database list only (add an
  in-market home-buyer audience), bidding is Maximize Conversions with no
  conversion data, and the final URL is the old listing page (lid 29957682).
  Swap the URL the day the relist page exists.
- Website: rayahmadi.com (Ray's team email runs on it and the live lead forms
  already point there). rayhomes.ca in the campaign files was wrong. Replaced
  in all active files.
- Retried the Meta lead-form campaign with the right link: still refused,
  code 31/3858385. Meta's hold needs Ray in Ads Manager on his own login.
  No tool here can do it. Retry is free, so retry at every daily loop.
- Hypothesis for the first read (Nov 14): the database-only audience is too
  small to spend $5/day. If spend is under $2/day, widen the audience.

---
## 2026-11-10 (evening) — Adspirer connected. Real account state read for the first time

- New connector: Adspirer (Google Ads 134-435-0136 and Meta account
  732663023528570). Free plan: 15 tool calls a month, 6 used today.
  search_tools and get_tool_schema are free. Failed calls did not count.
- Meta campaign 52506208679516 is PAUSED. No delivery in the last 30 days.
  That explains the lead form sitting at 27. It is a website-conversion
  campaign (pixel LEAD event, CBO $10/day, Stouffville +15 mi), not an
  instant-form campaign, and its one ad links to the listing page.
- Tried to add an instant-form ad set to it: Meta refused (all ad sets in a
  lowest-cost CBO campaign must share one optimization). A lead-form version
  needs its own campaign.
- Tried to create that campaign (34Buttonleaf-Stouffville-Leads, $5/day,
  Whitchurch-Stouffville city key 297205 + 25 km, form 985332827899566, video
  1553311682394230, no-address copy): Meta refused with code 31/3858385.
  Meta is holding a security check on Ray's Facebook user after the Nov 9
  logins. No ad can be created or edited by API until Ray authenticates in
  Ads Manager (Billing and payments, Start Authentication). Nothing was
  created.
- Google Ads: "Video ad - 34 Buttonleaf Cres" (Demand Gen, ID 24114799139,
  $5/day) exists and is PAUSED. Copy has no price and no address. It targets
  a 20-mile radius, presence only, but only the database retargeting list,
  and its final URL is the old listing page (lid 29957682), which may die at
  relist. "34 Buttonleaf | Stouffville | YouTube Views | 7D" (ID 24045317940)
  is paused at $0. Left both paused pending Ray's word and the new URL.
- 16 Curry Meta campaign 52506205424516: PAUSED today through Adspirer.
- Open question: campaign files use https://www.rayhomes.ca as the ad link.
  Ray's live ads use rayahmadi.com and rayrealestate.ca. Confirm the right
  domain with Ray before any ad is built with it.
- Lesson: read the live account before planning. Ten days of work assumed
  this campaign was live. It was paused the whole time.

---
## 2026-11-10 — Relist signed. Facebook connections broken. Ray: "we must sell"

- Authentisign "Signing complete" Nov 10, 9:26 AM: Form 242 Cancellation of
  Listing Agreement, new Form 271 Listing Agreement, and PropTx 290 MLS Data
  Form, signed by Ray and the seller. The listing is being cancelled and
  relisted as new. Not sold.
- Facebook invalidated every session on Nov 9 (Ray logged in with codes around
  4 PM). Result: Ad Advisor cannot reach the Page on either ad account
  (error 190/460), and the Pabbly workflow "34 Buttonleaf Cres - Lead form
  Automation" is paused with the same error. New Facebook leads are NOT
  reaching the CRM. They still sit in the Page's Leads Center.
- Lead form 985332827899566 was flat at 27 from Nov 3 to Nov 8. No newer read
  is possible until Meta is reconnected.
- The old ad links to the old listing page and prints the address. A relist
  gets a new MLS number and usually a new page URL, so the old ad is wrong
  twice over. Replace it on relist day with the no-address lead-form copy
  (already written in OPS-2026-11-03.json, op buttonleaf-no-address-copy).
- Decision: relist day is launch day. New-listing status is the strongest
  hook the property will get this year. Fresh ad, $5/day Meta, second video
  ad alongside it, YouTube $5/day from the launch pack.
- Lesson: one Facebook security reset silently broke ads access and the lead
  pipeline at the same time. Check Pabbly alerts and Ad Advisor status at the
  start of every daily loop, before reading any numbers.

---
## 2026-11-08 — Lead form flat for 5 days

- Live form read (Ad Advisor via account 1788128334781323): Buttonleaf form
  985332827899566 still at 27 lifetime leads, unchanged since Nov 3. Curry's
  form also unchanged at 23. Before Aug 20 Buttonleaf averaged about one lead
  a day, so the ad is most likely no longer delivering (paused, ended, or a
  billing hold). Cannot confirm: account 732663023528570 is still on the
  expired Ad Advisor link.
- Kill rules: not applicable without spend data.
- Action: none possible from here. Asked Ray to check Delivery in Ads Manager.

---
## 2026-11-04 — Listing activity from Ray's inbox (ad numbers still locked)

- Buyer-agent showings booked through BrokerBay: Oct 19, Oct 21, Oct 23,
  Oct 26, Nov 1. Offer presentation night Oct 21: one registered offer;
  sellers did not work with it. Documents signed on Authentisign Oct 26
  (type not visible in the subject line). Showings were still being
  booked after that, so treat the listing as active unless Ray says
  otherwise.
- Meta form 985332827899566 shows 27 lifetime leads (live read Nov 3).
  Spend since Aug 20 is unknown until the server report runs or Ad Advisor
  resets Nov 7.
- Improvement queued in campaigns/OPS-2026-11-03.json: second ad in the
  live ad set (the July "move-up" cut, no-address copy) so Meta has two
  ads to test; first ad's copy swapped to no-address; budget $5/day.

---
## 2026-11-03 — Priority listing

- Ray named Buttonleaf a priority on Nov 3. Already live. Server ops lower it to $5/day and swap in the no-address copy.

---
## 2026-11-03 — Creative audit: live ad shows the address

- Read from Ad Advisor's saved copy (as of Aug 20). The only live ad
  (52506208679716, "Over 4,000 Sq Ft of Luxury Living in Stouffville",
  one video) prints "34 Buttonleaf Cres, Whitchurch-Stouffville" in the
  primary text and links to the rayahmadi.com listing page. That breaks
  Ray's no-address rule and gives away the curiosity trade. The July
  7-day test ("See This Stouffville Move-Up Home") followed the rule; it
  ended Jul 27.
- Decision once Meta access is back: replace the copy with the no-address
  version in plan.md, lower budget to $5/day, add the other two Sid cuts
  so the ad set has 3+ ads.

---
## 2026-09-17 — Discovery: campaign has been LIVE since Jul 20 (via Ad Advisor)

- Correction to eight weeks of "nothing live" reports: the loop had no data
  feed and Ray never posted numbers. Ad Advisor (connected Sep 17) shows
  the campaign was launched from the ADMAX plan on Jul 20 and relaunched
  Aug 11. Lesson: a daily loop with no data source must say "no data
  source" and stop, never "nothing live."
- Sprint (Jul 20–27, campaign 6999756017312): 15s video, instant form
  only, Stouffville 15 mi, broad, $10/day, $105 cap. $64.41 spend,
  5 leads, CPL $12.88, CTR 3.1%. Ad copy was the ADMAX brief verbatim.
- Relaunch (Aug 11, campaign 52506208679516, ad set 52506208679316):
  one video ad, long listing-description copy WITH the address, pixel
  LEAD optimization (website + lead form), Stouffville 15 mi radius,
  home+recent location types, Advantage+ audience, interest signals
  (semi-detached, first-time buyer, detached home, real estate investing,
  Zillow). Aug 12–20: $88.73 spend, 8 leads, CPL $11.09, CTR 4.3–6.1%
  (one dip to 2.0% on Aug 19). No kill rule triggered.
- Hypothesis update: "withholding the address lowers CPL" is now
  testable — the sprint (no address) ran $12.88 CPL, the relaunch (address
  shown) $11.09. Too little volume to call; run both as variants.
- Structural gap vs. 2026 best practice: ONE ad per ad set. Andromeda
  wants 10–15 conceptually distinct creatives. This is the main upside.
- Lead quality unverified: 13 leads total, none inspected yet. Reading
  the form questions and the leads needs the Meta reconnect.


## 2026-07-19 — Day 0 (pre-launch)

- Status: plan v2 approved by Ray at $15/day ($10 Meta Leads, $5 YouTube
  Shorts). No price, no address in creative. Edit brief written for three
  vertical cuts from BUTTON LEAF (1).mp4.
- Open hypothesis 1: "fast cut" hook (best 1-second shot first) beats
  "POV walk-in" hook on CTR at equal impressions.
- Open hypothesis 2: withholding price/address lowers CPL vs. the priced
  version we would otherwise run (no control at this budget; judge
  against the $15 CPL target instead).
- Blockers to launch: cuts not yet produced (Sid's Media House or AI
  clipper); campaign not yet built in Ads Manager; Ad_Advisor connector
  not authorized, so daily data is manual until it is.
- Lesson carried in: none yet — first flight for this property.
