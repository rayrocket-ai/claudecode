# 34 Buttonleaf Cres — Campaign Plan (v2, approved 2026-07-19)

Playbook A: Listing Exposure — lean always-on variant. Approved by Ray.

## Budget

| Where | Daily | Objective |
|---|---|---|
| Meta (FB + IG, one campaign, automatic placements) | $10 | Leads (instant form) |
| YouTube Shorts | $5 | Views / retargeting pool |
| **Total** | **$15** | |

FB vs. IG is NOT split into separate campaigns: one Meta campaign serves
both, the auction allocates, and reporting still shows the split. Cut the
losing placement after 2 weeks of data.

## Strategy

- No price, no address in creative or copy. Curiosity play: the instant
  form offers "Get the price + address + full tour."
- Focus: Stouffville + the house type (detached, space, lot, lifestyle)
  to attract move-up buyers in the $1M–$2M band. Affordability cannot be
  targeted directly (Housing Special Ad Category); the form qualifiers
  and ARIA Voice follow-up do the filtering.
- Geo: Stouffville + 25 km radius — covers Markham, Aurora, Newmarket,
  Richmond Hill, Uxbridge (the move-up feeder ring). Broad within radius;
  creative is the targeting.
- Form qualifiers: (1) buying timeline, (2) pre-approved yes/no/in
  progress, (3) do you have a home to sell first (move-up flag).
- YouTube: Shorts placements, CPV bidding, same geo ring, contextual
  real-estate keywords/placements only (housing policy safe). Warms the
  audience; conversions happen on Meta.

## Expectations

- 2–5 leads/week after learning week. Meta CPL target $15, ceiling $30.
- YouTube ~100–150 views/day; judged as retargeting-pool growth only.
- Meta CPM benchmark $9–14 (GTA housing).

## Kill / decision rules (low-budget calibration)

- Judge variants on 7-day windows, not daily.
- Pause variant: CPL > $30 after $70+ spend.
- Replace variant: CTR < 0.8% after 2,000 impressions.
- Week 3: if YouTube adds nothing, propose folding $5 into Meta (Ray
  approves budget moves).

## Compliance

- Meta Housing Special Ad Category declared.
- eXp Realty branding on every ad and end card.
- No trending commercial audio in paid placements — Meta Sound Collection
  or royalty-free soundalikes only.
- No guaranteed claims. Fair-housing language check on all copy.
- Form links privacy policy; leads route to GHL with UTM tagging (CASL
  compliant follow-up).

## Tracking

- UTMs at ad level → GoHighLevel. CAPI via GHL for Meta. ARIA Voice
  speed-to-lead on every new lead.

## Daily learning loop

Owned by the `buttonleaf-campaign` agent, fired by a scheduled Routine
every morning at 8:00 Toronto time. Data → judge (kill rules) → append
learning-log.md → update dashboard.html + republish artifact → 3-line
report to Ray. Full protocol in .claude/agents/buttonleaf-campaign.md.
