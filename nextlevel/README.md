# Next Level

Draft build files. Version 1, written 2026-11-15 from Ray's Blueprint and Roadmap (dated 2026-10-29). Updated the same day with Ray's decisions of 2026-11-15.

Nothing in this folder is live. Every page, email, text and script here is a draft for Ray to review and approve before it is sent, published or loaded into HighLevel. The product names and the price ladder are approved (see "Decided by Ray, 2026-11-15" below).

## Tested offer

The offer was read to a fixed panel of 100 model-written personas in two rounds on 2026-11-15. The panel finds weak points. It is not market research and not a forecast: see `testing/README.md`. The round 2 pitch, `testing/offer-pitch-v2.md`, is now the working offer.

| Group | Measure | Round 1 | Round 2 |
|---|---|---|---|
| 70 agents, founding price | Buys | 0 | 3 |
| | Books a call | 7 | 19 |
| | Passes | 63 | 48 |
| 70 agents, standard price | Buys | 0 | 1 |
| | Books a call | 2 | 9 |
| 30 business owners | Joins waitlist | 1 | 5 (one is a competitor) |
| All 100 | Would refer someone | 4 | 11 |
| Agents | Trust in Ray, out of 5 | 2.8 | 2.7 |

- Round 1: [testing/offer-round1/RESULTS.md](testing/offer-round1/RESULTS.md)
- Round 2: [testing/offer-round2/RESULTS.md](testing/offer-round2/RESULTS.md)
- How to run the next round: [testing/LOOP.md](testing/LOOP.md)

These are simulated people. The real test is the first 10 sales calls, recorded in the scoreboard in `testing/LOOP.md`.

**Terms set after the test.** Set 2026-11-15 after the persona test; Ray to confirm. Ray said "fix and heal and make it better", so the assistant set the round 2 terms and carried them into `offer.md`, the sales files, the content rules and the build spec. They are not approved by Ray. In each file they carry that marker where they first appear. In short: usage at cost with no markup for founders, with a monthly cap the client sets and Ray's own bill shown on the call; the agent dials the live system on the call; English at launch, other languages tested on the client's line with no charge if not good enough; no contact with a client's callers, the transcript stays in the client's account, recording off by default and announced when on, export and deletion on leaving; a text and email summary for every call, with a direct CRM push confirmed before payment; a one-page brokerage summary and the first month back if the brokerage says no within 14 days; a callback and a text alert on urgent calls; forwarding only when unanswered and switched off on cancel; one subscription per business line, teams quoted; other businesses open after the first 10 agents are live, in the stated order, from $500 setup plus $400 a month; Canada first, US confirmed per state. Full wording: `offer.md` section 6.

## Still open

Facts only Ray can supply. The round 2 test showed these are what still stops a buyer. Each one stays a placeholder in the files until he answers. They are listed in the order to answer them.

1. The usage rate per minute, as a number. And whether "at cost, no markup" leaves an acceptable margin at $300.
2. The languages the AI handles today.
3. Which CRMs get a direct push.
4. The registered business name and address (also needed in every footer and email under CASL).
5. Where data is hosted.
6. Team pricing.
7. Which US states.
8. A waitlist date.
9. Whether to offer a smaller plan for very small practices.

Ray also confirms or changes each term marked "Set 2026-11-15 after the persona test; Ray to confirm".

Open from before the test:

10. Calendar booking link for the 15-minute call.
11. HighLevel webhook address for the sales page quiz.
12. Trademark check on "Next Level", Canada and US.
13. Stripe verification.
14. Legal and licence checks already flagged:
   - CASL basis for the missed-call audit email.
   - Separate entity for Next Level, and eXp sign-off.
   - Repliers licence for client accounts.
   - Dari on the voice agent.
   - Whether the HighLevel plan includes SaaS mode and rebilling.

## Decided by Ray, 2026-11-15

- **Product names.** Next Level Answer (AI receptionist), Next Level Reviews, Next Level Nurture, Next Level Ads, Next Level Complete. Approved by Ray, 2026-11-15. They replace "ARIA".
- **Price ladder after the Founding 10 (CAD).** Answer $500 setup + $400 a month. Reviews $250 setup + $150 a month. Nurture $500 setup + $250 a month. Ads $500 setup + $750 a month, with ad spend on the client's own card. Complete $1,500 setup + $1,500 a month. Approved by Ray, 2026-11-15. The Founding 10 price stays $300 a month for Answer.
- **Who sells.** Ray is the seller and the closer on every call for now. Nadiya later.
- **Proof.** Ray Homes is the proof for now. The Founding 10 opens now, on Ray's own track record and a live demo of the system running on Ray Homes.
- **Main marketing goal.** Inbound. Businesses and agents reach out to Next Level because of content on every platform. See `content/`.
- **HighLevel sub-account.** Verified: name "Next Level", location ID n0qwGpNQ3CShe8AIhyI0 (seen in HighLevel's notices to Ray's inbox on 2026-11-15).
- **Founding 10 terms.** Approved by Ray, 2026-11-15, as proposed. No setup fee for founders. The $300 a month price stays locked while the subscription is active. Month to month, cancel before the next billing date, contacts exported on exit. Live within 7 days of the client supplying everything needed, or the first month is not charged (once per client, first month only, not for carrier or registration delays). Feedback calls at day 14 and day 30. A client's numbers are shared only with written permission. See `offer.md` section 6.
- **NL Demo sub-account.** Approved by Ray, 2026-11-15. A demo sub-account named "NL Demo" with made-up contacts only. See `saas-build-spec.md` section 2a. Creating it is a step in `ghl-location-setup.md`.
- **Secondary channels.** Approved by Ray, 2026-11-15, managed in Slack. Agents Ray knows, rooms where agents gather, and partners are kept. They are run through Slack, with Viktor (the Slack assistant that holds the HighLevel connection) managing the HighLevel side under its propose-only rule. See `offer.md` section 1.
- **Welcome video.** Ray chose an AI-made video for new clients. The script is a draft for his approval: `onboarding/welcome-video-script.md`.

## Check

- A contact import ran into the "Next Level" sub-account on 2026-11-15. HighLevel reported 88% deliverable and 10% high risk.
- Ray Homes consumer contacts must not be emailed about Next Level.
- Ray to say which list it was. Until he does, no email or text goes to those contacts from this sub-account.

## Slack

- Next Level approvals are posted in #nextlevel-approvals (private channel, id C0CHSJFA146). Ray Homes content stays in #agent-marketing. A piece goes to exactly one of them.
- Next Level stays in the same Slack workspace as Ray Homes for now, because the connections and Viktor live there.
- Revisit a separate workspace when Next Level has its own staff.

## What Next Level is

Next Level is Ray Ahmadi's AI automation service for real estate agents, sold as a monthly subscription and delivered on HighLevel.

Ray Homes Real Estate is client zero. Every system is built and run on Ray's own business first. Then it is sold to real estate agents across North America as a simple offer. Then it goes to other businesses, one industry at a time.

Next Level replaces the old product name "ARIA".

## How people find Next Level

The main goal for marketing is inbound. Businesses and agents reach out to Next Level because of content on every platform. The content plan and drafts are in `content/`.

Inbound content sends people to the smart sales page and the quiz, then to the 15-minute call with Ray. Business owners outside real estate who reach out join the waitlist until their industry opens (see the gate rule).

The missed-call audit is a secondary, optional tactic. It is kept as drafted in `sales/missed-call-audit.md`.

## The one-line promise

Every call answered, qualified and booked, live in 7 days.

That is the promise for the first offer, the AI receptionist. The wider promise for the brand: systems a working broker runs on his own business, set up for yours.

## The proof we lead with

Ray Homes is the proof for now. These are the only track-record facts to state:

- GTA real estate broker.
- Ray Homes Real Estate under eXp Realty.
- 12+ years.
- About 50 deals a year.
- Multi-year eXp Icon agent.
- Bilingual, English and Dari.

Then the live demo of the system running on Ray Homes. System metrics (calls answered, bookings, reviews, replies) are shown live on the call. Where a file needs a specific system metric in writing, it keeps the placeholder `[Ray to add: real number from Ray Homes]`. No other number is used.

## The numbers we are building toward

These are goals, not results.

- Goal for the SaaS: 500 users.
- First target: 10 paying agents by end of January (the "Founding 10").
- $3,000 monthly recurring revenue from the Founding 10.
- Churn under 5%.

## The gate rule

Nothing moves to the next phase until its gate is met.

1. Ray's own business proves each offer before an agent pays for it. For the first offer this gate is resolved by Ray on 2026-11-15: the Founding 10 opens now, on Ray's own track record and a live demo of the system running on Ray Homes. Rungs 2 to 5 are released one at a time, each after it runs on Ray Homes.
2. Each new industry starts only when real estate has paying clients and a repeatable onboarding.

For other businesses, the round 2 offer states the gate in a buyer's words: Answer opens once the first 10 agents are live. (Set 2026-11-15 after the persona test; Ray to confirm.)

This rule decides the build order below. It also decides what the "for businesses" edition can and cannot do today. See `offer.md`.

## How the folder is organized

| File | What it is | Who uses it |
|---|---|---|
| `README.md` | This file. Status and build order. | Ray, Diana |
| `offer.md` | The offer: who, problem, promise, product ladder, founding terms, approved prices, objections. | Ray, Nadiya later |
| `saas-build-spec.md` | How it is built in HighLevel: SaaS mode, the sales sub-account, the master snapshot, onboarding, retention, weekly numbers. | Ray, Diana, builder |
| `ghl-location-setup.md` | Numbered steps to create the "Next Level" sub-account and connect it. | Ray or Diana |
| `onboarding/welcome-video-script.md` | Script, on-screen text, shot list and production notes for the AI-made welcome video. DRAFT for Ray's approval. | Ray, Diana |
| `content/` | Inbound content for every platform. The primary lead source. | Ray, Diana |
| `sales/funnel-copy.md` | The smart sales page: headlines, quiz, result blocks, offer, FAQ, call to action. | Ray, builder |
| `sales/page/` | The built sales page. Not yet updated to the round 2 terms. | Ray, builder |
| `sales/missed-call-audit.md` | The free missed-call audit: method, log, email, voice note. Secondary, optional tactic. | Ray, Diana |
| `sales/call-script.md` | The 15-minute call. | Ray. Nadiya later. |
| `sales/follow-up-emails.md` | Four follow-up sequences by problem, with the CASL sender block. | Ray, Diana |
| `product-roadmap.md` | One-page roadmap in four phases, from the Founding 10 to a licence for others. | Ray |
| `testing/` | The 100-persona panel, the two pitch files, the results of both rounds and `LOOP.md`, the steps to rerun the test. | Ray, Diana |
| `learning/course-notes-template.md` | Empty note-taking template for any training the team owns. | Ray's team |
| `learning/course-notes-digest.md` | Digest of Ray's course notes, in our own words, section by section. | Ray, Diana |
| `learning/apply-map.md` | Each lesson mapped to where it lands in Next Level, with status. Where the notes and Ray's decisions differ. How the one-person company system runs it. | Ray |
| `learning/content-additions.md` | Content ideas, hooks, lead magnets and outreach drafts from the notes, to be merged into `content/`. | Ray, Diana |
| `learning/open-questions.md` | What the notes leave unanswered, and the next lessons worth taking. | Ray |

## What we took from the course notes

Added 2026-11-15. Ray's notes on a training course he is enrolled in were read in full and applied. Next Level is Ray's own product on his own platform. It is not connected to the course or its author, and no income figure, student result or template from the course is used anywhere in this folder.

- `learning/course-notes-digest.md`: what the notes say, in our own words.
- `learning/apply-map.md`: where each idea landed, what conflicts with Ray's decisions, and which AI team does what.

What changed in these files (each change is marked "Added from the course notes, 2026-11-15"):

| File | What was added |
|---|---|
| `offer.md` | Secondary channels and the first-contact rule (section 1). One plain line per rung (section 3). Optional founder review at day 30 (section 6). Three objections (section 11). The five-test product check (section 12). |
| `saas-build-spec.md` | Three working sub-accounts and the version 1 scope (section 1). The NL Demo sub-account (section 2a). The build and test standard for every workflow, the reminder branch, the review request rule and the parked ideas (section 3). Welcome video, client agreement and client user access (section 8). Script review measure (section 12). |
| `sales/call-script.md` | First-contact rule, pre-call brief, what to listen for, the after-hours question, the one-line version, three short objection answers, the after-call summary step, the script review. |
| `sales/follow-up-emails.md` | Three one-off emails: after-call summary, lead magnet delivery, the day after meeting in person. |

Nothing approved was changed: brand, platform, product names, prices, who sells, the proof and the inbound-first plan all stand. Every addition that is a suggestion is marked `PROPOSED, Ray to approve`. Since then Ray has approved the secondary channels and the NL Demo sub-account (see "Decided by Ray, 2026-11-15").

New questions for Ray from this work are in `learning/open-questions.md`. The main ones still open: set the script review numbers, and confirm with counsel the consent basis for any message to a person who has not asked.

## Build order

1. **Unblock.** Stripe verification. Legal name and mailing address for Next Level. Trademark check on the name in Canada and the US.
2. **Show the proof.** Keep the AI receptionist running on Ray Homes and keep the demo line ready for every call. The Founding 10 opens now. Collect the real system numbers as they come in.
3. **Finish the sales sub-account.** Step 1 (create it) is verified: "Next Level", location ID n0qwGpNQ3CShe8AIhyI0. The remaining steps in `ghl-location-setup.md` still apply, including creating the NL Demo sub-account.
4. **Build the master snapshot.** Follow `saas-build-spec.md`. Build it on Ray Homes first, then save it as the snapshot.
5. **Build the sales machine.** Sales page and quiz, follow-up workflows, booking calendar, checkout.
6. **Publish inbound content.** Content on every platform, so businesses and agents reach out. See `content/`. This is the primary lead source.
7. **Sell the Founding 10.** One human step: the 15-minute call. Ray is the seller and the closer on every call for now. Nadiya later.
8. **Onboard and retain.** Snapshot clone, the 9-step checklist, day 3 and day 14 checks, usage alerts, monthly report.
9. **Release the next rungs.** One at a time, each after it runs on Ray Homes. The prices are approved.
10. **Open the business edition.** Only after the gate. Mortgage brokers first.

Optional, any time after step 5: the missed-call audit. 20 GTA agents, weekdays 7 to 9 PM. Its legal flags must be cleared first. See `sales/missed-call-audit.md`.

## Status

| Item | Status | Owner | Note |
|---|---|---|---|
| Blueprint and Roadmap | Done | Ray | Dated 2026-10-29 |
| HighLevel agency, Founder plan, "Next Level" logo | Done | Ray | SaaS mode and rebilling still to check. See spec. |
| Voice agent prompt "John" on HighLevel Voice AI | Done (existing asset) | Ray | Needs prompt slots for the snapshot |
| "Move Planner" smart sales page | Done (existing asset) | Ray | Consumer page for Ray Homes. Not the Next Level page. |
| Missed-call audit plan, 5-step pitch script, hand-raiser emails | Done (existing assets) | Ray | Drafts in `sales/` build on them |
| Database of 17,686 contacts in HighLevel | Done (existing asset) | Ray | Proof ground for the reactivation campaign. Not a Next Level sales list. |
| Draft files in this folder | Done (draft) | Claude | Waiting on Ray's review |
| Product names to replace ARIA | **Approved by Ray, 2026-11-15** | Ray | Answer, Reviews, Nurture, Ads, Complete. See `offer.md` section 4. |
| Pricing beyond the founding offer | **Approved by Ray, 2026-11-15** | Ray | See `offer.md` section 7. |
| Who sells | Decided by Ray, 2026-11-15 | Ray | Ray is the seller and the closer on every call for now. Nadiya later. |
| Proof that opens the Founding 10 | Decided by Ray, 2026-11-15 | Ray | Opens now, on Ray's track record and a live demo on Ray Homes. |
| Main marketing goal | Decided by Ray, 2026-11-15 | Ray | Inbound content on every platform. See `content/`. |
| "Next Level" sub-account in HighLevel | **Verified, 2026-11-15** | Ray or Diana | Name "Next Level", location ID n0qwGpNQ3CShe8AIhyI0, seen in HighLevel's notices to Ray's inbox on 2026-11-15. Funnel link and calendar link still to send. Remaining steps are in `ghl-location-setup.md`. |
| Contact import into the "Next Level" sub-account | **Check** | Ray | Ran on 2026-11-15. HighLevel reported 88% deliverable, 10% high risk. Ray to say which list it was. Ray Homes consumer contacts must not be emailed about Next Level. |
| NL Demo sub-account | **Approved by Ray, 2026-11-15**, not created yet | Ray or Diana | Made-up contacts only. Step in `ghl-location-setup.md`. |
| Secondary channels | **Approved by Ray, 2026-11-15, managed in Slack** | Ray, with Viktor | Viktor manages the HighLevel side under its propose-only rule. See `offer.md` section 1. |
| Welcome video for new clients | Draft script, waiting on Ray | Ray | AI-made video. Script in `onboarding/welcome-video-script.md`. Made only after Ray approves the script in Slack with the clapper reaction. |
| Next Level approvals in Slack | Done | Ray | #nextlevel-approvals, id C0CHSJFA146. Same workspace as Ray Homes for now. |
| Calendar booking link and HighLevel webhook address | Waiting on Ray | Ray or Diana | See "Still open" |
| Stripe verification | **Blocked** | Ray | Blocks every SaaS sale and the checkout link |
| System metrics from Ray Homes | Waiting on Ray | Ray | Every "[Ray to add: real number from Ray Homes]" in these files. Does not block the Founding 10: the copy leads with the track record and the live demo. |
| Founding 10 usage | Set 2026-11-15 after the persona test; Ray to confirm | Ray | Billed at cost with no markup, up to a cap the client sets. The rate per minute and the margin at $300 are still open. See "Still open". |
| Round 2 terms in the offer, sales, content and build files | Set 2026-11-15 after the persona test; Ray to confirm | Ray | See "Tested offer". Not approved by Ray. The built page in `sales/page/` does not carry them yet. |
| Offer test, rounds 1 and 2 | Done | Claude | 100 personas. Results in `testing/`. |
| Founding 10 terms, including the live-in-7-days commitment | **Approved by Ray, 2026-11-15** | Ray | Exact terms in `offer.md` section 6. Copy states them only as written there. |
| Trademark check on "Next Level", Canada and US | **Blocked** (not checked) | Ray, with counsel | Do this before paid ads, a domain or printed material |
| Business name and mailing address for Next Level | Waiting on Ray | Ray | Needed in every email under CASL |
| Call recording and AI disclosure rules per province or state | Waiting on Ray | Ray, with counsel | Needed before any client goes live |
| Business edition | Waiting on the gate | Ray | Designed into the snapshot now. Sold later. |

## Rules for anyone working in this folder

- No invented results, testimonials, client counts, rates or prices. The only set prices are $300 a month for the Founding 10 AI receptionist and the approved ladder in `offer.md` section 7.
- The only track-record facts to state are the six listed under "The proof we lead with".
- No income or earnings claims. No guarantees unless Ray approves the exact terms. The one approved commitment is live in 7 days or the first month is not charged, stated only with its exact terms from `offer.md` section 6.
- CASL applies to every email and text.
- Nothing is sent, published or changed in HighLevel without Ray's approval.
- Markers used in these files:
  - `Approved by Ray, 2026-11-15`: a decision. Do not change it without Ray.
  - `PROPOSED, Ray to approve`: a suggestion, not a decision.
  - `Set 2026-11-15 after the persona test; Ray to confirm`: a term the assistant set after the offer test, under Ray's instruction to fix the offer. Used in copy as the working offer. Not approved by Ray.
  - `[Ray to ...]`: Ray must supply or confirm this.
  - `[verify in HighLevel]` and `[verify menu name]`: check in the live account before relying on it.
