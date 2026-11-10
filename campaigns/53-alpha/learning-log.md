# 53 Alpha Court — Woodbridge — Learning Log

Every test gets: hypothesis, variants, spend, result, decision, lesson.
Newest entries at the top.

---
## 2026-11-10 (late) — Ray: execute. Seller approved relist + $10,000 agent bonus

- Seller approved Ray's plan at 10:37 AM: relist at the same price, ads on
  Facebook, Instagram and YouTube, flat $10,000 buyer-agent bonus for an
  accepted offer by Nov 24. Ray told the seller the campaign launches the day
  the listing goes live and promised regular updates. Ray to me: start
  running ads on YouTube and Facebook.
- YouTube: confirmed running. Campaign 24273515703, $5/day, YouTube only,
  presence-only geo, ad group "Alpha | Vaughan | Homebuyers", link
  rayahmadi.com/contact.
- Facebook: NOT live. Two blocks. (1) Ad Advisor's token for account
  1788128334781323 is invalid since Nov 9 (provenance: token_invalid), and
  that account is not connected to Adspirer. (2) Meta's security hold on
  Ray's login blocks ad edits by API anyway.
- Copy error caught before launch: the paused ad 120250513340880620
  (creative 2145526649387908) says "A pool." and "three-bedroom apartment".
  Ray's own email to the seller says "pool-sized yard" and "walkout lower
  level with its own entrance". Treat Ray's wording as the truth. New copy is
  in plan.md. The old ad must not be switched on as is. Thumbnail hash of
  the video for the rebuild: de12bad50dc4b58fc8e053349b1b2a19.
- Lesson: check ad claims against what Ray tells the seller before launch.
  A wrong feature claim on a $2M listing is a complaint waiting to happen.

---
## 2026-11-10 (evening) — YouTube is already live for Alpha

- Google Ads campaign "53 Alpha Court | YouTube In-Market | CAD5 | Sep 2026"
  (ID 24273515703, VIDEO, $5/day) is ENABLED. Last 30 days: $148.75 spent,
  23 clicks, 0 tracked conversions. So the YouTube half of the $10/day plan
  has been running since September. No change made.
- Several older Alpha campaigns sit paused in the same account (IDs
  23485439458, 23095237597, 23091114365, 23085204372, 21507215037).
- Meta ad 120250513340880620 (account 1788128334781323) is still paused.
  That account is not connected to Adspirer, and Meta's security hold on
  Ray's Facebook user (code 31/3858385) blocks ad edits by API anyway.
- Next: Ray clears the Meta security check, then says go.

---
## 2026-11-10 — Seller agreed to relist. Ad still paused. Ray: "we must sell"

- Seller replied Nov 10 to Ray's Nov 7 market update: agrees to relist at the
  same price. Asked three things: what extra marketing will boost the new
  listing, whether a higher buyer-agent commission would help, and whether
  the lower of the two interested buyers can be moved up.
- Draft reply written for Ray in Gmail (not sent). It answers the marketing
  question with the paid plan. Commission and negotiation are Ray's calls
  and are left as blanks for him to fill.
- Ad 120250513340880620 is still built and PAUSED. It cannot be switched on
  from here today: Facebook invalidated every session on Nov 9, so Ad
  Advisor lost the Page on this account too (error 190/460).
- Decision: launch on relist day so the ad and the new MLS listing land
  together. Needs Ray's "go" plus the Meta reconnect (or Ray flips the three
  switches in Ads Manager himself).
- Hypothesis unchanged: the golf-course and basement-apartment hooks carry
  this one. First test once two ads are live.

---
## 2026-11-07 — Ad set and first ad built (paused, waiting on Ray's preview)

- Ad set 120250513336680620: $5/day, Vaughan + 25 km, instant form, Advantage+
  audience and placements. Ad 120250513340880620 with creative 2145526649387908.
- Video: 876779404654435, the 2024 upload "53 alpha court video tour" (9:16,
  34 s) already in ad account 1788128334781323. Used because the new Sep 2026
  cuts cannot reach Meta until the Drive folders are link-shared or the
  server runs. Copy is the no-price, no-address version; form 1112543945036414.
- Kept PAUSED: Ray has not seen this 2024 video in the new campaign. One tap
  to go live once he approves (campaign, ad set, ad). The server ops file
  still adds the two Sep 2026 cuts to this same ad set and then switches it on.
- Main account 732663023528570 (Buttonleaf, Curry) is still on the expired
  Ad Advisor link, so no Buttonleaf numbers or fixes today.

---
## 2026-11-04 — Listing activity from Ray's inbox

- Showings booked: Oct 17, Oct 18, Oct 20, Oct 23, and a new request for
  today (Nov 4, 5:30 PM, REN/TEX Realty). Offer emailed Oct 25 by a buyer
  through Nadiya. Seller thread Oct 26 on backyard water accumulation and
  offer conversations. A REALTOR.ca information request Oct 17 and a
  potential client callback Oct 19.
- Takeaway: organic and MLS demand is real. The Meta campaign adds local
  buyers who are not yet working with an agent; launch is queued (ad set,
  two tour videos, then ON) in the server ops file.

---
## 2026-11-03 — Priority listing

- Ray approved promoting 53 Alpha on Nov 3 ('buttonleaf and alpha lets promote this'). The server ops file now switches it ON right after the ad set and two video ads are built.

---
## 2026-11-03 — Built in Meta (partial, paused)

- Ad account 1788128334781323 (the second "Ray Ahmadi" account; the only one with a
  live Ad Advisor link today). Page: Ray Homes Team. Instagram: rayahmadi.
- Campaign 120250450871140620: OUTCOME_LEADS, Housing (CA), PAUSED, $200 lifetime spend cap.
- Lead form 1112543945036414: higher-intent (review step), intro card, name / email /
  phone + timeline, pre-approval, home-to-sell. Privacy:
  rayahmadi.com/privacy-policy. Thank-you button to rayahmadi.com (not the
  listing page, so the address stays behind the form).
- NOT built yet: the ad set ($5/day, 25 km radius, instant form) and the
  ads. Ad Advisor's plan limit (20 actions/month) ran out on this call.
  Resets 2026-11-07, or Ray upgrades the plan, or Ray adds the ad set in
  Ads Manager by hand.

---
## 2026-11-03 — Day 0 (drafted)

- Ray asked for this listing on Nov 3, together with 85 Sidney Rundle,
  97 Jackman and the already-live 34 Buttonleaf. 16 Curry retired (sold).
- Plan mirrors Buttonleaf and Curry ($15/day: $10 Meta Leads, $5 YouTube
  Shorts; no price, no address). One change from those two: launch with
  6 to 10 creatives in one ad set, not one ad.
- Open hypothesis 1: the "golf-course lot" hook out-pulls the generic
  tour cut on CTR. It is the rarest feature and self-selects the buyer.
- Open hypothesis 2: the "basement apartment" hook produces the
  highest-quality leads (pre-approved, 30-to-90-day timeline).
- Blockers: Ray's budget approval; Meta access (Ad Advisor reconnect or
  META_ACCESS_TOKEN in environment secrets plus graph.facebook.com on the
  network allowlist); creative cuts where noted in plan.md.
- Lesson carried in from Buttonleaf and Curry: the curiosity trade works
  (CPL $11 to $12 on one ad each). Never got to A/B test hooks because
  only one ad ran. Fix that here from day one.
