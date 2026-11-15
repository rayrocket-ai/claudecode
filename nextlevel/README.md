# Next Level

Draft build files. Version 1, written 2026-11-15 from Ray's Blueprint and Roadmap (dated 2026-10-29). Updated the same day with Ray's decisions of 2026-11-15.

Nothing in this folder is live. Every page, email, text and script here is a draft for Ray to review and approve before it is sent, published or loaded into HighLevel. The product names and the price ladder are approved (see "Decided by Ray, 2026-11-15" below).

## Tested offer

The offer was read to a fixed panel of 100 model-written personas in three rounds on 2026-11-15. The panel finds weak points. It is not market research and not a forecast: see `testing/README.md`. The round 3 pitch, `testing/offer-pitch-v3.md`, is the working offer. Approved by Ray, 2026-11-15: Ray said yes to it.

All 100 personas, founding price:

| Measure | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| Buys | 0 | 3 | 7 |
| Books a call | 7 | 19 | 12 |
| Joins a list | 1 | 5 | 8 |
| Passes | 92 | 73 | 73 |
| Would refer someone | 4 | 11 | 21 |
| Trust in Ray, out of 5 | 2.7 | 2.7 | 2.8 |
| Buys at the standard price ($500 setup plus $400 a month) | 0 | 1 | 2 |

- Round 1: [testing/offer-round1/RESULTS.md](testing/offer-round1/RESULTS.md)
- Round 2: [testing/offer-round2/RESULTS.md](testing/offer-round2/RESULTS.md)
- Round 3: [testing/offer-round3/RESULTS.md](testing/offer-round3/RESULTS.md)
- Facts behind round 3, and what is not verified: [testing/facts-round3.md](testing/facts-round3.md)
- How to run the next round: [testing/LOOP.md](testing/LOOP.md)

What round 3 showed:

- The 7 buyers were five Canadian agents, one GTA mortgage agent and one Etobicoke renovation company owner.
- The minute bundle closed the usage question. It fell from 23 mentions to 1.
- Stated limits cost call bookings (19 to 12) and moved people who cannot be served, such as US agents, onto a list.
- The losses that remain are limits of the product today (languages, the US, data location) and the absence of client results. More wording will not move them.

These are simulated people. The real test is the first 10 sales calls, recorded in the scoreboard in `testing/LOOP.md`.

**Round 3 terms. Approved by Ray, 2026-11-15.** They are carried into `offer.md`, the sales files, the content rules and the build spec, and they replace the round 2 terms. In short:

1. **Usage.** The $300 founding price includes 250 AI call minutes, the phone number and up to 500 text segments a month. Extra minutes are $0.30 CAD each. A part minute counts as a minute, unused minutes do not carry over, minutes are shown on each invoice, and the client sets a monthly cap, which can be zero. The same bundle and extra-minute price apply at the standard price.
2. **Founding spots.** 3 of the 10 are open now to mortgage brokers and to contractors and renovators, on the same founding terms. 7 are for real estate agents. Real estate lawyers, accountants and insurance open on 1 March 2027, with first notice to the waitlist.
3. **Teams.** Each additional agent line on the same account is half the monthly price ($150 founding, $200 standard) and adds 125 minutes to a shared pool.
4. **Geography.** Founding clients are in Canada only. US agents can join a US list and are told the opening date and the US dollar price by 1 March 2027.
5. **Adopted wording, no new number.** A demo number on the page before the call (the number is still to be supplied). A written agreement before payment that names the registered business. Never recruiting a client to Ray's brokerage or team. "There is no cheaper plan today." The data and transcript wording. The language wording: English, plus the listed languages after a test on the client's line, with Dari, Farsi, Punjabi, Mandarin, Cantonese, Urdu and Arabic not promised. The CRM wording: a one-way push through Zapier for Follow Up Boss and BoldTrail, Lofty and Sierra Interactive tested in set-up, and a text and email summary for everything else.

Full wording: `offer.md` section 6.

## Verify before publishing

Ray approved the offer. Nobody has verified the facts under it. On 2026-11-15 no official HighLevel page could be opened, so everything below came from search-result text (`testing/facts-round3.md`). In the files each one is marked `[not verified]`. None is published as checked until it has been checked in the HighLevel account or on its help pages.

| # | Not verified | What the files rely on | Where to check it |
|---|---|---|---|
| 1 | Every HighLevel rate | The per-minute Voice AI engine and speech rates, the language model cost, the phone rate per minute, the text rate per segment and its carrier fee, the number rent, and the transcription charge. They are the basis of the 250-minute bundle and the $0.30 extra minute. | In the account: the agency billing and wallet screens, and the usage lines on Ray Homes' own invoice. [verify menu name] On the help pages: the "AI Product Pricing Update" article and the "Phone System Pricing & Billing Guide" on help.gohighlevel.com. |
| 2 | The language list | French, Spanish, Hindi, German, Portuguese, Italian, Dutch, Russian and Japanese beside English. | In the account: the Language picker on the Voice AI agent. On the help pages: "Multi-language support for Voice AI agents". Then one test call in each language offered. |
| 3 | The hosting statement | "HighLevel says its infrastructure is in the United States, on Google Cloud and Amazon Web Services, and it publishes a SOC 2 Type II report." | On the help pages: "HighLevel Security and Compliance Overview" and the SOC 2 Type II article, and the privacy and security page on gohighlevel.com. |
| 4 | The CRM connection method | A one-way push through Zapier (HighLevel's Zapier app is called LeadConnector) for Follow Up Boss and BoldTrail, with Lofty and Sierra Interactive tested in set-up. | In the account: build the workflow that fires when a Voice AI call ends and send one real test call into each CRM. On the help pages: "How to create Voice AI agents". Also confirm the Zapier plan and its cost. |

Two behaviours must be tested in the account before the first client. No source confirmed either one.

| # | Behaviour | The test |
|---|---|---|
| 5 | Recording stays off unless switched on | Make a test call on a Voice AI line with recording off. Confirm no audio file exists afterwards and that the transcript and summary still arrive. If they do not, the promise in `offer.md` changes before anyone is sold on it. |
| 6 | The system stops at the client's cap | Set a low cap in NL Demo and use it up. Confirm the AI stops taking calls, the alert arrives, and the phone rings through as before. If no setting does this, write down how the cap is enforced by hand. |

The arithmetic behind the bundle is in `saas-build-spec.md` section 13. It rests on two assumptions: a language model cost of one US cent a minute, and 1 USD = 1.40 CAD. Recheck the margin against a real invoice after the first month.

## Still open

Facts only Ray can supply, and one test. Each one stays a placeholder in the files until he answers. They are listed in the order to answer them.

1. The registered business name and address. They go on the agreement, and in every footer and email under CASL.
2. The demo phone number. The page line "a demo number is on the page" is not used until it exists.
3. Whether HST is added to the prices.
4. The names of the set-up team. They are named in the agreement.
5. A second-language test on Ray's own line. This is the persona test's biggest remaining lever: 22 of 100 serve callers in a language that is not promised. A passed test in even one of Punjabi, Mandarin or Farsi would open that group.
6. The US opening date and the US dollar price. The US list is told both by 1 March 2027.
7. Calendar booking link for the 15-minute call.
8. HighLevel webhook address for the sales page quiz.
9. Stripe verification.
10. Trademark check on "Next Level", Canada and US.
11. Legal and licence checks already flagged:
   - CASL basis for the missed-call audit email.
   - Separate entity for Next Level, and eXp sign-off.
   - Repliers licence for client accounts.
   - Call recording and AI disclosure rules for each client's province.
   - What the AI may say, record and send for a mortgage broker, before the first mortgage client goes live.
   - Whether the HighLevel plan includes SaaS mode and rebilling.

Two smaller gaps the round 3 offer leaves, noted here so they are not answered by accident: what happens past 500 text segments in a month, and whether an extra agent line carries a setup fee at the standard price.

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
- **Round 3 offer.** Approved by Ray, 2026-11-15. The minute bundle and the $0.30 extra minute, the 3 founding spots for mortgage brokers and for contractors and renovators, team lines at half price with a shared pool, Canada only with a US list, and the adopted wording. See "Tested offer" above and `offer.md` section 6. The facts under it are not verified: see "Verify before publishing".

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

Inbound content sends people to the smart sales page and the quiz, then to the 15-minute call with Ray. Mortgage brokers and contractors and renovators take the same quiz and call, for the 3 founding spots open to them. Other business owners who reach out join the waitlist until their industry opens (see the gate rule).

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
- First target: 10 paying agents by end of January (the "Founding 10"). Since 2026-11-15 the 10 founding spots are 7 for real estate agents and 3 for mortgage brokers and for contractors and renovators.
- $3,000 monthly recurring revenue from the Founding 10.
- Churn under 5%.

## The gate rule

Nothing moves to the next phase until its gate is met.

1. Ray's own business proves each offer before an agent pays for it. For the first offer this gate is resolved by Ray on 2026-11-15: the Founding 10 opens now, on Ray's own track record and a live demo of the system running on Ray Homes. Rungs 2 to 5 are released one at a time, each after it runs on Ray Homes.
2. Each new industry starts only when real estate has paying clients and a repeatable onboarding.

**A decided exception to rule 2. Approved by Ray, 2026-11-15.** 3 of the 10 founding spots are open now to mortgage brokers and to contractors and renovators, on the same founding terms as agents. 7 are for real estate agents. Real estate lawyers, accountants and insurance open on 1 March 2027, with first notice to the waitlist. Any other business can join the waitlist, and no date is promised. Outside this exception the rule holds: no ad or outbound message is aimed at a non-agent industry, and nothing is sold to an industry before its date.

This rule decides the build order below. It also decides what the "for businesses" edition can and cannot do today. See `offer.md` section 1.

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
| `sales/page/` | The built sales page. A separate pass is bringing it to the round 3 offer. Check it against `offer.md` section 6 before it is published. | Ray, builder |
| `sales/missed-call-audit.md` | The free missed-call audit: method, log, email, voice note. Secondary, optional tactic. | Ray, Diana |
| `sales/call-script.md` | The 15-minute call. | Ray. Nadiya later. |
| `sales/follow-up-emails.md` | Four follow-up sequences by problem, with the CASL sender block. | Ray, Diana |
| `product-roadmap.md` | One-page roadmap in four phases, from the Founding 10 to a licence for others. | Ray |
| `testing/` | The 100-persona panel, the three pitch files, `facts-round3.md`, the results of all three rounds and `LOOP.md`, the steps to rerun the test. | Ray, Diana |
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
10. **Open the business edition.** Mortgage brokers and contractors and renovators are open now, within 3 founding spots. Real estate lawyers, accountants and insurance open on 1 March 2027. Everything else waits for the gate.

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
| Round 3 offer in the offer, sales, content and build files | **Approved by Ray, 2026-11-15** | Ray | See "Tested offer". Usage is a bundle: 250 AI call minutes, the number and up to 500 text segments in the $300, extra minutes $0.30 CAD, a cap the client sets. |
| Facts under the round 3 offer | **Not verified** | Ray or Diana | HighLevel rates, the language list, the hosting statement and the CRM connection method came from search-result text. See "Verify before publishing". |
| Cap and recording behaviour | **Not tested** | Ray or Diana | Both must be tested in the account before the first client. See "Verify before publishing". |
| Offer test, rounds 1 to 3 | Done | Claude | 100 personas. Results in `testing/`. |
| Founding 10 terms, including the live-in-7-days commitment | **Approved by Ray, 2026-11-15** | Ray | Exact terms in `offer.md` section 6. Copy states them only as written there. |
| Trademark check on "Next Level", Canada and US | **Blocked** (not checked) | Ray, with counsel | Do this before paid ads, a domain or printed material |
| Business name and mailing address for Next Level | Waiting on Ray | Ray | Needed in every email under CASL |
| Call recording and AI disclosure rules per province or state | Waiting on Ray | Ray, with counsel | Needed before any client goes live |
| Business edition | Partly open. **Approved by Ray, 2026-11-15** | Ray | 3 founding spots for mortgage brokers and for contractors and renovators, now. Real estate lawyers, accountants and insurance on 1 March 2027. The rest waits on the gate. |

## Rules for anyone working in this folder

- No invented results, testimonials, client counts, rates or prices. The only set prices are $300 a month for the Founding 10 AI receptionist, the approved ladder in `offer.md` section 7, and the round 3 numbers in `offer.md` section 6: $0.30 CAD for an extra minute, and $150 or $200 a month for an extra agent line.
- The only track-record facts to state are the six listed under "The proof we lead with".
- No income or earnings claims. No guarantees unless Ray approves the exact terms. The one approved commitment is live in 7 days or the first month is not charged, stated only with its exact terms from `offer.md` section 6.
- CASL applies to every email and text.
- Nothing is sent, published or changed in HighLevel without Ray's approval.
- Markers used in these files:
  - `Approved by Ray, 2026-11-15`: a decision. Do not change it without Ray.
  - `PROPOSED, Ray to approve`: a suggestion, not a decision.
  - `[not verified: ...]`: a fact taken from search-result text on 2026-11-15, not from an official page or the account. It is checked before the line is published. See "Verify before publishing".
  - `Set 2026-11-15 after the persona test; Ray to confirm`: retired. It marked the round 2 terms. Ray approved the round 3 offer on 2026-11-15, and the files listed in "Tested offer" no longer carry it.
  - `[Ray to ...]`: Ray must supply or confirm this.
  - `[verify in HighLevel]` and `[verify menu name]`: check in the live account before relying on it.
