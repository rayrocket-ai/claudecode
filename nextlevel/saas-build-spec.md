# Next Level: SaaS build spec (HighLevel)

Draft for Ray, Diana and whoever builds. This is a plan, not a record of what exists. Nothing here changes a live workflow, agent, pipeline or contact until Ray approves it.

Anything marked `[verify in HighLevel]` is something we are not sure HighLevel supports natively, or supports on Ray's plan. Check it in the live account before building on it.

## 1. Agency settings and SaaS mode checklist

Work through this in the agency view. Tick each line only when seen on screen.

- [ ] Confirm the plan. The Blueprint says "Founder plan". Confirm this plan includes SaaS mode, snapshots, rebilling and unlimited sub-accounts. [verify in HighLevel]
- [ ] Agency profile: name "Next Level", logo, support email, support phone. [Ray to confirm: business name and mailing address for Next Level]
- [ ] White-label domain for the app login (for example app.yourdomain). [Ray to set: domain for Next Level] [verify in HighLevel]
- [ ] White-label mobile app or the standard app: decide. [verify in HighLevel]
- [ ] Stripe connected at agency level. **Blocked until Stripe verification is done.**
- [ ] SaaS mode switched on and the SaaS configurator open. [verify in HighLevel]
- [ ] Products and prices created in Stripe for each SaaS plan (section 6).
- [ ] Rebilling switched on for phone, SMS, email and AI (section 7).
- [ ] Phone system: confirm the built-in phone service is active at agency level and can be resold to sub-accounts. [verify in HighLevel]
- [ ] Messaging registration: confirm what each sub-account must file before texts send (business texting registration for US numbers, and anything required for Canadian numbers). [verify in HighLevel]
- [ ] Email: confirm the built-in email service is active and each sub-account can have its own sending domain. [verify in HighLevel]
- [ ] Voice AI available to sub-accounts and included in snapshots. [verify in HighLevel]
- [ ] Agency-level users: Ray (owner), Diana (admin). Nadiya gets access to the sales sub-account only.
- [ ] Default snapshot for new SaaS sign-ups set to the Next Level master snapshot. [verify in HighLevel]
- [ ] Terms of service and privacy policy links for checkout. [Ray to confirm with counsel]
- [ ] Three working sub-accounts exist and are named clearly: Ray Homes (Ray's own business, where everything is proven), Next Level (sales, section 2) and NL Demo (section 2a). Client accounts come after these. (Added from the course notes, 2026-11-15.)

**Out of scope for version 1.** (Added from the course notes, 2026-11-15.) Leave these parts of the platform alone until the Founding 10 are live: memberships and courses, the app marketplace, blogs, media storage. The work is the workflows, the voice agent and the CRM. The community in section 2 is the one exception already planned. Whether it also waits: [Ray to decide].

## 2. The "Next Level" sales sub-account

This is where Next Level sells Next Level. It is separate from the Ray Homes sub-account. Creation steps are in `ghl-location-setup.md`.

It holds:

**The funnel**
- Smart sales page with the quiz (copy in `sales/funnel-copy.md`).
- Result page per problem.
- Booking page for the 15-minute call.
- Checkout page (Stripe). Blocked until Stripe verification.
- Thank-you page that starts onboarding.
- Waitlist form and US list form. Each has a consent checkbox that is not pre-ticked.

**The quiz**
- 6 questions plus a contact step: name, email, biggest problem.
- Consent checkbox for email, not pre-ticked.
- Writes the problem to a custom field and a tag.

**Pipeline: Next Level Sales**

| Stage | Enters when | Leaves when |
|---|---|---|
| Lead | Quiz submitted (inbound content is the primary source), or audit call logged (optional tactic) | Audit email sent, or call booked |
| Audit sent | Missed-call audit email sent | Call booked |
| Call booked | 15-minute call on the calendar | Call held |
| Won | Payment received | Intake form sent |
| Onboarding | Intake form sent | Step 9 of the checklist done |
| Live | Go-live confirmed | Stays here |
| At risk | Any churn signal in section 11 | Back to Live, or cancelled |

**Calendars**
- "Next Level 15-minute call". Ray takes every call for now. Nadiya added later. Round robin when both are on. [verify in HighLevel]
- "Onboarding call". Diana or Ray.
- "Day 3 check" and "Day 14 check". Short calls or a logged message.

**Follow-up workflows**
- One per problem: missed calls, reviews, dead database, ads. Three emails each (copy in `sales/follow-up-emails.md`).
- Each stops the moment a call is booked.
- Each sends only to contacts who ticked the consent box.
- Booked-call reminder workflow.
- No-show workflow: one message, then a task for the closer (Ray, for now).
- Won workflow: sends the intake form, creates the onboarding tasks, moves the stage.

**The community**
- Free "AI for Agents" group on HighLevel Communities. [verify in HighLevel]
- Joining the community is not consent to marketing email. Keep the two separate.

## 2a. The NL Demo sub-account

Approved by Ray, 2026-11-15. Added from the course notes, 2026-11-15. Ray or Diana creates it: see Part J and the done checklist in `ghl-location-setup.md`.

- A third sub-account, named "NL Demo", cloned from the master snapshot, holding made-up contacts only. No real person's name, number or call is in it.
- Use: Ray shares this screen on the 15-minute call to show the pipeline, a call summary and the monthly report. The live call to the receptionist still goes to the real line.
- Why: showing the Ray Homes account on a shared screen puts real callers' names and numbers in front of a stranger. Ray Homes numbers can still be read out or shown as totals with contact details off screen.
- Label every made-up record "sample" so nobody mistakes it for a result.
- It is also the place to test every snapshot change before it reaches a client.

## 3. The master snapshot, item by item

Build it and run it on Ray Homes first. Save it as the snapshot only when it works there.

### Naming convention

- Everything Next Level ships starts with `NL`.
- Custom values: `nl_` then group then name, lower case, underscores. Example: `nl_biz_name`.
- Custom fields: `NL | ` then a plain label. Example: `NL | Caller reason`.
- Tags: `nl-` then group then value, lower case, hyphens. Example: `nl-source-ai-call`.
- Workflows: `NL 01 | Missed-call text-back`. The number is the rung and order.
- One edition word where it matters: `agent` or `biz`.

### Pipelines

**NL | Client pipeline (agent edition)**
New caller > Qualified > Appointment booked > Appointment held > Client > Closed > Not a fit

Stage names are the part that changes per industry (section 4).

### Custom values (set once per client, used everywhere)

| Custom value | Holds |
|---|---|
| `nl_edition` | `agent` or `biz` |
| `nl_industry` | real estate, mortgage, law, accounting, contracting, insurance |
| `nl_biz_name` | Business or team name |
| `nl_owner_name` | The person callers ask for |
| `nl_brokerage_name` | Brokerage, firm or parent company as it must appear |
| `nl_service_area` | Cities or areas served |
| `nl_hours` | Office hours |
| `nl_phone_main` | Main number |
| `nl_transfer_number` | Where a live transfer goes |
| `nl_booking_link` | Client's calendar link |
| `nl_review_link` | Google review link |
| `nl_mailing_address` | For the CASL footer |
| `nl_ai_name` | Name the voice agent uses |
| `nl_ai_disclosure_line` | The exact words the agent uses to say it is an AI |
| `nl_recording_line` | The exact words about call recording, if recording is on |
| `nl_languages` | Languages the agent handles |
| `nl_faq_1` to `nl_faq_5` | Top questions and approved answers |
| `nl_not_allowed` | What the agent must never answer (price opinions, legal, mortgage or tax advice) |
| `nl_appointment_name` | What a booking is called: showing, consultation, estimate |

`nl_ai_disclosure_line` and `nl_recording_line` are filled only after the rules are confirmed for that client's province or state. [Ray to confirm with counsel]

### Custom fields (per contact)

- NL | Caller reason (buy, sell, rent, listing question, other)
- NL | Timeline
- NL | Area of interest
- NL | Preferred language
- NL | Qualified (yes, no, unknown)
- NL | Call summary
- NL | Consent basis (express, implied, none) and NL | Consent date
- NL | Review requested date, NL | Review received
- NL | Last AI call date

### Tags

- Source: `nl-source-ai-call`, `nl-source-missed-call`, `nl-source-form`, `nl-source-ad`
- Status: `nl-status-qualified`, `nl-status-booked`, `nl-status-needs-human`
- Consent: `nl-consent-express`, `nl-consent-implied`, `nl-do-not-contact`
- Reviews: `nl-review-requested`, `nl-review-received`
- Campaign: `nl-reactivation-sent`, `nl-hand-raiser`

### Calendars

- "Call with {{custom_values.nl_owner_name}}". One calendar, connected to the client's Google or Outlook.
- Buffer, notice and hours come from the intake form.

### The voice agent and its prompt slots

Start from the existing "John" prompt on HighLevel Voice AI. Turn every client-specific detail into a slot filled from custom values.

| Slot | Filled from |
|---|---|
| Identity and greeting | `nl_ai_name`, `nl_biz_name` |
| AI disclosure | `nl_ai_disclosure_line` |
| Recording notice | `nl_recording_line` |
| What the business does and where | `nl_industry`, `nl_service_area` |
| Hours | `nl_hours` |
| Qualifying questions | Edition block (section 4) |
| Booking | Calendar action, `nl_appointment_name` |
| Approved answers | `nl_faq_1` to `nl_faq_5` |
| Never answer | `nl_not_allowed` |
| Hand-off to a person | `nl_transfer_number` |
| Close and summary | Writes the call summary field and moves the stage |

- Whether Voice AI prompts can read custom values directly, or must be pasted per client: [verify in HighLevel]
- Whether the voice agent copies inside a snapshot: [verify in HighLevel]
- Listing lookup through Repliers ("is this home still available?"): needs a custom action from the voice agent to an outside service. [verify in HighLevel] Agent edition only.
- Languages: English is live today. The other languages offered are the ones in the Language picker on the voice agent. [not verified: the list of French, Spanish, Hindi, German, Portuguese, Italian, Dutch, Russian and Japanese came from search-result text; read the picker in the account] Dari, Farsi, Punjabi, Mandarin, Cantonese, Urdu and Arabic are not promised. Whether the agent can change language by itself in the middle of a call: [verify in HighLevel]

### Workflows in the snapshot

| Number | Workflow | What it does | Rung |
|---|---|---|---|
| NL 01 | Missed-call text-back | Call not answered: one text to the caller with the booking link. Business hours rule set by client. | Answer |
| NL 01 | AI call finished | Writes summary, sets fields and tags, moves stage, notifies the client. | Answer |
| NL 01 | Needs a human | Creates a task and alerts the client at once. | Answer |
| NL 01 | Speed-to-lead | New form or ad lead: instant text and email, then an AI call or a call task. [verify in HighLevel: outbound AI calls] | Answer, Ads |
| NL 01 | Appointment reminders | Confirmation at booking. Reminder one day before, asking for a reply to confirm. No reply: one reschedule message with the booking link and a task for the client. (Branch added from the course notes, 2026-11-15.) | Answer |
| NL 02 | Review request at closing | Triggered when the stage moves to Closed. | Reviews |
| NL 02 | Review request at day 30 | Second request 30 days after closing, only if no review yet. | Reviews |
| NL 02 | Review reply draft | New review arrives: AI drafts a reply for the client to approve. Never auto-posts. [verify in HighLevel] | Reviews |
| NL 03 | Reactivation campaign | Messages past contacts who have a valid consent basis. Replies go to the client. | Nurture |
| NL 03 | Hand-raiser follow-up | Anyone who replies with interest gets a task and a booking link. | Nurture |
| NL 03 | Past-client touches | Scheduled check-ins for past clients. | Nurture |
| NL 00 | Unsubscribe and STOP handling | Applies `nl-do-not-contact`, stops every workflow. | All |
| NL 00 | Monthly report | Builds and sends the client report (below). | All |

All workflows ship switched off. They are turned on during onboarding, one at a time.

### Build and test standard for every workflow

Added from the course notes, 2026-11-15. Check each line before a workflow goes into the snapshot.

**Settings**
- Re-entry: decided and written in the workflow description. Off for one-time messages (review request at closing). On where the same contact can trigger it again (missed-call text-back).
- Stop on response: on for every sequence that sends more than one message. A reply ends the sequence and creates a task.
- Sending window: set for every workflow that texts or emails. No messages outside the hours the client set. [Ray to set: default sending hours]
- Triggers: list every trigger in the description. A workflow can have several, and a forgotten one is the usual cause of a surprise send.

**Testing**
1. Save and publish in NL Demo, never in a client account.
2. Run a manual test with a sample contact. Remember that a manual test skips the trigger conditions.
3. Then fire the real trigger (submit the form, miss the call, move the stage) and confirm the contact enrolled.
4. Test the after-hours case: a form filled at 10 PM on a Friday. What does the lead receive, and when?
5. Open the enrollment history and the execution log. Confirm the contact reached the last step and did not stall at a wait or a branch.
6. Reply STOP as the sample contact. Confirm every workflow ends.
7. Run the promise tests in section 13 before any client account goes live, and again after every snapshot change.

### Review requests: one rule

Added 2026-11-15. The course notes describe a review request that first asks for a rating and sends only the high ratings to the public review page. Next Level does not build that. Every client who is asked receives the same public review link. A private "tell us what went wrong" option may be offered to everyone alongside it. Reason: sorting people by rating before the public ask is commonly restricted by review platforms. [verify against Google's current review policy] [Ray to confirm with counsel]

### Parked ideas from the course notes

Not built and not priced. Each needs Ray's decision before any work starts.

- Website chat that books to the calendar. Could sit inside Answer.
- Auto-reply to social comments and direct messages. Could sit inside Nurture.
- Invoicing for clients.
- A check that the client's name, phone, address, hours and services read the same on their website and their Google Business Profile. Could be one line on the Reviews intake.
- Claiming the business profile that AI assistants show. The notes say the process was not confirmed with the provider. [verify] before it is offered to anyone. It applies to Ray Homes first.

Every email carries the sender name, mailing address and unsubscribe link. Every text names the sender and honours STOP. The client is the sender for messages from their sub-account.

### Forms

- Client intake form (used in onboarding step 2).
- Website contact form.
- Buyer and seller inquiry forms (agent edition).
- Every form has a consent checkbox that is not pre-ticked.

### Dashboard

One dashboard per sub-account: calls received, calls answered by the AI, appointments booked by the AI, missed-call texts sent, new contacts, reviews requested and received. [verify in HighLevel: which of these are native dashboard widgets]

### Client-facing monthly report

Sent on the same day each month. One page.

- Calls received, calls answered by the AI.
- Appointments booked by the AI.
- Missed calls that got a text back.
- Reviews requested and received (if on Reviews).
- One thing we changed this month.
- One thing we suggest next.

Only real numbers from their account. No estimates of money earned or saved. Whether this can be scheduled natively or needs a manual send: [verify in HighLevel]

## 4. One snapshot, two editions

The snapshot is the same. Four things change per industry.

| What changes | Agent edition | Business edition |
|---|---|---|
| Voice prompt (qualifying block) | Buying, selling or renting. Area. Timeline. Working with an agent already. | Service needed. Timeline. Existing client or new. Industry rules on what cannot be said. |
| Pipeline stage names | New caller > Qualified > Appointment booked > Appointment held > Client > Closed > Not a fit | Mortgage: New inquiry > Qualified > Call booked > Application > Funded > Not a fit. Others follow the same shape. |
| Custom values | `nl_edition` = agent, `nl_appointment_name` = showing or consultation, brokerage name required | `nl_edition` = biz, `nl_appointment_name` = consultation or estimate, firm name |
| Review links | Agent's Google Business Profile | Business's Google Business Profile, or the platform that matters in that industry |

Everything else is shared: workflows, tags, fields, forms, dashboard, report.

How to hold the two editions:

- **PROPOSED, Ray to approve:** one master snapshot with `nl_edition` as the switch, and one small prompt file per industry kept outside the snapshot. Reasoning: one thing to maintain. A fix made once reaches every client.
- If HighLevel cannot switch stage names or prompts by custom value, fall back to one snapshot per industry, cloned from the master. [verify in HighLevel]

Gate reminder, with the exception decided by Ray. Approved by Ray, 2026-11-15: 3 of the 10 founding spots are open now to mortgage brokers and to contractors and renovators, so the mortgage and contractor prompt blocks and stage names are needed before the first of those clients goes live. Real estate lawyers, accountants and insurance open on 1 March 2027. No other business sub-account is created for a paying or free client before its industry opens.

## 5. Listing data (agent edition only)

- Repliers feeds listing status so the agent can answer "is this home still available?"
- Whether one Repliers licence can serve client sub-accounts, and in which boards: [Ray to confirm: Repliers licence terms for client accounts]
- Until confirmed, the voice agent takes a message on listing questions and books a call.

## 6. SaaS plans mapped to the product ladder

Create these in the SaaS configurator. How many plans the configurator allows: [verify in HighLevel]

| SaaS plan in HighLevel | Product | Price | Status |
|---|---|---|---|
| NL Answer Founding | Next Level Answer, Founding 10 | $300 a month, including 250 AI call minutes, the phone number and up to 500 text segments | Ready to create once Stripe is verified. Cap at 10 sales: 7 real estate agents, 3 mortgage brokers or contractors and renovators. |
| NL Answer | Next Level Answer | $500 setup + $400 a month | Approved by Ray, 2026-11-15 |
| NL Reviews | Next Level Reviews | $250 setup + $150 a month | Approved by Ray, 2026-11-15 |
| NL Nurture | Next Level Nurture | $500 setup + $250 a month | Approved by Ray, 2026-11-15 |
| NL Ads | Next Level Ads | $500 setup + $750 a month, with ad spend on the client's own card | Approved by Ray, 2026-11-15 |
| NL Complete | Next Level Complete | $1,500 setup + $1,500 a month | Approved by Ray, 2026-11-15 |

All prices in Canadian dollars. Product names and prices: Approved by Ray, 2026-11-15. Rungs 2 to 5 are created now and released one at a time (see `offer.md` section 8).

- Each plan switches on only the features that rung needs, so a Reviews client does not see the voice agent. [verify in HighLevel]
- Setup fees: whether the configurator can charge a one-time fee with a plan, or needs a separate Stripe product: [verify in HighLevel]
- A hard cap of 10 on the founding plan may need to be done by hand (hide the checkout after sale 10). The split of 7 and 3 is counted by hand too. [verify in HighLevel]
- Extra agent lines. Approved by Ray, 2026-11-15: $150 a month at the founding price and $200 a month at the standard price, each adding 125 minutes to a shared pool. Whether this is an add-on to a plan or a second plan: [verify in HighLevel]
- Founding clients are in Canada only. No checkout is shown to a US buyer. (Approved by Ray, 2026-11-15.)

## 7. Rebilling

Approved by Ray, 2026-11-15. Usage with Next Level Answer is a bundle, at the founding price and at the standard price. It replaces every earlier usage rule in this section.

| Usage | What the client pays | Check |
|---|---|---|
| AI call minutes, up to 250 a month (plus 125 for each extra agent line) | Included in the monthly price | [verify in HighLevel: a plan with a minute allowance] |
| AI call minutes past the allowance | $0.30 CAD each, up to the monthly cap the client sets. The cap can be zero. | [verify in HighLevel: fixed-rate rebilling for Voice AI minutes, and whether it can be charged in Canadian dollars] |
| Phone number | Included | [verify in HighLevel] |
| Text segments, up to 500 a month | Included | [verify in HighLevel: a plan with a text allowance] |
| Text segments past 500 a month | Not decided | [Ray to set: text segments past 500] |
| Email | Not decided | [Ray to set] |
| Usage on Reviews, Nurture, Ads and Complete | Not decided | [Ray to set: usage terms for rungs 2 to 5] |

- A part minute counts as a minute. Unused minutes do not carry over. Minutes used are shown on each invoice. Build requirements are in section 13.
- Rebilling needs Stripe connected and a card on file in each sub-account. Blocked until Stripe verification.
- Each sub-account has a prepaid balance that refills. With a bundle, decide whether the client sees a balance at all. [Ray to set: starting balance and refill amount] [verify in HighLevel]
- The voice on this plan is one of the lower-cost voices. The premium voice that the cost table in section 13 excludes is not used on this plan.
- HighLevel's own rates are never quoted to a buyer as Next Level's rate. The buyer's number is the bundle.
- Tell every client in writing, before they pay, what is included and what an extra minute costs.

## 8. The 9-step onboarding checklist

PROPOSED, Ray to approve. Goal: live in 7 days. The live-in-7-days commitment itself is approved by Ray, 2026-11-15: live within 7 days of the client supplying everything needed, or the first month is not charged (once per client, first month only, not for carrier or registration delays). Feedback calls at day 14 and day 30 are also approved for founders.

1. **Agreement, payment and welcome.** Approved by Ray, 2026-11-15: the client gets a written agreement before payment. It names the registered business and its address, and the set-up team. [Ray to confirm with counsel: the client agreement] [Ray to confirm: business name and mailing address for Next Level] [Ray to add: names of the set-up team] Then payment is received. Welcome email sent with the intake form and the onboarding call link. Stage moves to Won, then Onboarding. Added from the course notes, 2026-11-15: the welcome email also carries one short welcome video (what happens in the 7 days, what the form asks, how to reach us). Ray chose an AI-made video, 2026-11-15. The script is in `onboarding/welcome-video-script.md`, DRAFT for Ray's approval.
2. **Intake form back.** Business details, hours, areas, top questions, who gets hand-offs, calendar, number to forward, the monthly cap on extra minutes (it can be zero), the name of their CRM and the languages their callers use. The 7 days start here.
3. **Sub-account cloned.** New sub-account created from the Next Level snapshot. Client user added. The client user sees the features of the rung they bought and nothing half-built. They are told in writing what else exists and when it opens. The client connects their own Google, Facebook and Instagram accounts while logged in as themselves. Next Level never asks for or stores a client's passwords. (Added from the course notes, 2026-11-15.)
4. **Custom values filled.** Every `nl_` value entered and read back.
5. **Phone ready.** Number bought or forwarding set from the client's current number. Messaging registration filed if required.
6. **Calendar connected.** Client's calendar linked. A test booking made and removed.
7. **Voice agent set.** Prompt slots filled. AI disclosure line and recording line confirmed for the client's province. [Ray to confirm with counsel] Internal test calls done. If the client's CRM is Follow Up Boss, BoldTrail (kvCORE), Lofty or Sierra Interactive, the client authorises the Zapier connection and a test record is sent. If that push does not work, the client can cancel and is not charged.
8. **Client test and sign-off.** The client calls their own line, hears the agent, asks for changes, approves. Any language other than English is tested here, on the client's own line, with the client. If it does not handle their callers to their standard, the account does not go live and no charge is made.
9. **Go live.** Forwarding on. Missed-call text-back on. Client logged into the app. Day 3 and day 14 checks booked. Stage moves to Live.

## 9. Day 3 and day 14 checks

**Day 3**
- Has the agent answered at least one real call?
- Listen to the calls. Any wrong answers, any caller who got stuck?
- Are bookings landing on the right calendar?
- Are missed-call texts sending?
- Has the client opened the app?
- Fix what is wrong the same day. Send the client a short note with what was fixed.

**Day 14**
- Calls received, calls answered by the AI, appointments booked by the AI.
- Has the client had a first win? (Definition in section 12.)
- Two questions for the client: what is working, what is annoying.
- Update the prompt from real calls.
- Founders: feedback call.
- If no first win by day 14, tag the account At risk and call the client.

## 10. Usage alerts

Set these as internal notifications to Ray and Diana.

- No calls reaching the agent in [Ray to set: threshold] days. Forwarding may be off.
- Prepaid balance low or card declined.
- A client's minutes reach the allowance (250, plus 125 for each extra line), or reach the cap they set.
- A spike in calls marked "needs a human".
- Text or email delivery failing.
- Client has not logged in for [Ray to set: threshold] days.

Whether these can be triggered across sub-accounts from the agency view, or need a check by hand each week: [verify in HighLevel]

## 11. Churn signals

Any one of these moves the account to At risk and creates a task to call the client.

- Call forwarding switched off.
- No first win within 7 days of go-live.
- Zero appointments booked by the AI in a month.
- Payment failed.
- Client asks how to export contacts or cancel.
- Client stops opening the monthly report.
- Complaint from one of the client's callers about the AI.

Retention tools from the Blueprint: usage alerts, the monthly results report, referral rewards. [Ray to set: the referral reward]

## 12. What to measure weekly

One short table, same day each week.

| Measure | Definition |
|---|---|
| Monthly recurring revenue | Sum of active monthly subscriptions. Setup fees and usage are not included. |
| Churn | Clients who cancelled in the period divided by clients active at the start. The goal is under 5%. [Ray to confirm: per month] |
| First win within 7 days | Share of new clients whose AI booked an appointment or captured a qualified caller within 7 days of go-live. PROPOSED definition, Ray to approve. |
| Calls answered | Calls answered by the AI across all client accounts, and as a share of calls received. |
| Appointments booked by AI | Bookings made by the voice agent across all client accounts. |

Also watch, from the sales side: inbound inquiries by platform, lead magnet requests by post, quiz completions, calls booked, calls held, Won. Audits sent, if the optional audit is run.

Script review, added from the course notes, 2026-11-15, PROPOSED: after every [Ray to set: number] calls held, compare calls held to Won. If the share is below [Ray to set: threshold], the script is rewritten before more calls are taken. Objections logged in the contact notes are the input.

No targets are set here beyond the ones in the Blueprint: 10 paying agents by end of January, $3,000 monthly recurring revenue from the Founding 10, churn under 5%.

## 13. Promises the build must keep

The round 3 offer (`testing/offer-pitch-v3.md`) is the working offer. Approved by Ray, 2026-11-15. Each term is a promise made to a buyer, so each one is a build requirement here. Full wording: `offer.md` section 6.

Ray approved the offer. The platform has not been checked against it. A promise marked `[verify in HighLevel]` depends on the platform. If the check comes back "no", the promise is kept by hand with a written procedure, or the wording in `offer.md` changes before anyone is sold on it. No client goes live on a promise that has not been checked.

| # | Promise | What the build must do | Check |
|---|---|---|---|
| 1 | The bundle: the monthly price includes 250 AI call minutes, the phone number and up to 500 text segments | The NL Answer Founding plan and the NL Answer plan each carry the allowance. Usage inside it is not billed to the client. The summary and alert texts are kept short enough that a normal month stays inside 500 segments. | [verify in HighLevel: a plan with a minute and text allowance, and what the client sees] |
| 2 | Extra minutes are $0.30 CAD each, at the founding price and at the standard price | Minutes past the allowance are billed at a fixed rate of $0.30 CAD, not at a percentage of cost. | [verify in HighLevel: fixed-rate rebilling per Voice AI minute, in Canadian dollars] |
| 3 | The cap: the client sets a monthly cap on extra minutes, and it can be zero. The system stops and alerts the client | The cap is entered at intake and stored as `nl_usage_cap`, in minutes. When the allowance plus the cap is used, the AI stops taking calls, the client is alerted by text and email, and calls ring through to the client's own phone or voicemail as they did before. With the cap at zero the bill cannot pass the monthly price. | [verify in HighLevel: a per-account minute cap with a stop. No source confirmed this setting exists. Must be tested before the first client] |
| 4 | The shared team pool: each extra agent line is half the monthly price ($150 founding, $200 standard) and adds 125 minutes, and all lines on the account share one pool | One account holds every line. The allowance is 250 plus 125 for each extra line, stored as `nl_minutes_included`. Minutes are counted across all lines against that one figure. | [verify in HighLevel: several numbers or agents in one sub-account counted against one allowance] |
| 5 | Minute rounding: a part minute counts as a minute, and unused minutes do not carry over | The minute count on the client's statement rounds each call up to the next full minute. The count returns to zero at each billing date. | [verify in HighLevel: how call length is rounded in the usage report, and when the count resets] |
| 6 | Invoice display: minutes used are shown on each invoice | Each invoice, or a statement sent with it, shows minutes included, minutes used and extra minutes billed. | [verify in HighLevel: whether the invoice can show minutes used] |
| 7 | Ray's own usage shown on the call | The usage view for the Ray Homes account can be shown on a shared screen with no caller details in view. | [verify in HighLevel] |
| 8 | A demo number on the page before the call, and a live dial on the call | A demo line that is always on, answers as an AI, and holds no real contacts. It is tested before every sales call. The page line is not published until the number exists. | [Ray to add: demo phone number] |
| 9 | A written agreement before payment that names the registered business | The agreement is sent and accepted before the checkout link. It names the registered business and its address, and the set-up team. Every footer carries the same name and address. | [Ray to confirm: business name and mailing address for Next Level] [Ray to add: names of the set-up team] [Ray to confirm with counsel: the client agreement] |
| 10 | English live today. A listed language is switched on at the client's request and tested first. Dari, Farsi, Punjabi, Mandarin, Cantonese, Urdu and Arabic are not promised | Onboarding step 8 holds the language test: the client calls their own line in each language their callers use and signs off, or the account does not go live and no charge is made. `nl_languages` lists only languages that passed. | [verify in HighLevel: the Language picker list] [not verified: the language list came from search-result text] |
| 11 | No contact with a client's callers, and no recruiting | No agency-level workflow, campaign or list reads a client sub-account's contacts. Nothing is copied from a client account into the Next Level or Ray Homes accounts. No client is added to any Ray Homes or eXp recruiting list. Both clauses are in the client agreement. | [Ray to confirm with counsel: the client agreement] |
| 12 | A transcript is read by the client, and by the set-up team only during set-up or a fix the client asked for | Staff reach a client account through a named user with the lowest role that does the job. Access is opened for set-up or for a fix the client asked for, then removed. Every access is logged with the date and the reason. No AI tool outside the platform reads client transcripts. If one ever does, the data wording in `offer.md` changes first. | [verify in HighLevel: access control for staff, per sub-account, with a log] |
| 13 | Where data is held: HighLevel, in the United States, not in Canada | Nothing in the build says or implies Canadian storage. The data wording is used as written in `offer.md` section 6. | [not verified: the hosting statement and the SOC 2 Type II report came from search-result text; read the help pages] |
| 14 | Audio recording off unless the client turns it on | Call recording is off in the snapshot and in every new account. Turning it on is the client's choice, made in writing. The transcript and summary must still be produced with recording off. | [verify in HighLevel: recording off on a Voice AI line while the transcript is still produced. No source confirmed it. Must be tested before the first client. If it fails, the wording changes to a recording that is deleted within a day] |
| 15 | Recording announced when on | When recording is on, `nl_recording_line` is filled and the AI says it at the start of every call. When recording is off, the line is empty and nothing is recorded. | [Ray to confirm with counsel] |
| 16 | Export and deletion within 30 days of leaving | An offboarding procedure: export contacts and transcripts to the client, confirm they received the file, delete both from the account within 30 days of the day they leave, then close the account. | [verify in HighLevel: export and deletion of transcripts] |
| 17 | Summary by text and by email | The "AI call finished" workflow sends the summary to the client by text and by email after every call. | Test call |
| 18 | CRM: a one-way push through Zapier for Follow Up Boss and BoldTrail (kvCORE). Lofty and Sierra Interactive tested in set-up. Text and email summary for everything else. No extra charge | A workflow that fires when a Voice AI call ends and sends the caller and the summary to Zapier. One Zap per CRM, authorised by the client. It creates or updates a contact or lead and reads nothing back. If the push for one of the four fails in set-up, the client can cancel and is not charged. Sierra Interactive may need fields a caller did not give. | [verify in HighLevel: the call-ended trigger and the Zapier action] [not verified: the connection method came from search-result text; none of the four has been tested] [Ray to confirm: the Zapier plan and who pays for it] |
| 19 | One-page brokerage summary, first month back if the brokerage says no within 14 days | The one-page summary exists as a file. A refund procedure exists for the first month and is logged on the contact. | [Ray to confirm: the day the 14 days are counted from] |
| 20 | Urgent-call callback and text alert | When a caller asks for a person or the call is urgent, the AI offers a callback, the "Needs a human" workflow texts the client at once, and a task is created. The copy promises a callback and an alert. It does not promise a live transfer, so `nl_transfer_number` is used only where a transfer has been tested. | Test call |
| 21 | Forwarding only when unanswered, including when the phone is off | Forwarding is set as conditional: no answer, busy and unreachable. It is never set to forward every call. | [verify in HighLevel: call forwarding conditions] [verify with the client's carrier] |
| 22 | Forwarding off on the day of cancelling | The offboarding procedure removes forwarding on the cancel date and a test call confirms the client's phone rings as before. | Test call |
| 23 | It only answers calls that come in. It does not place sales calls | No outbound AI call is switched on in a Next Level Answer account. In the speed-to-lead workflow the outbound AI call step stays off and the call task is used. | Test in NL Demo |
| 24 | Founding spots: 7 for real estate agents, 3 for mortgage brokers and for contractors and renovators. Real estate lawyers, accountants and insurance on 1 March 2027 | The founding checkout closes at 10 sales, with the 7 and the 3 counted by hand. The waitlist form has a consent box that is not pre-ticked and one question: industry and biggest phone problem. No checkout exists for a real estate lawyer, an accountant or an insurance business before 1 March 2027. | Form test |
| 25 | Founding clients in Canada only. A US list, told the opening date and US dollar price by 1 March 2027 | No US client account is created. The US list form has a consent box that is not pre-ticked. One message goes to that list by 1 March 2027. | Form test. [Ray to set: US opening date and US dollar price] |

Custom values for the snapshot: `nl_usage_cap` (the monthly cap on extra minutes the client chose, zero allowed), `nl_minutes_included` (250, plus 125 for each extra agent line), `nl_lines` (the number of agent lines on the account), `nl_recording_on` (yes or no, default no), `nl_summary_email` and `nl_summary_mobile` (where summaries and alerts go), `nl_crm_name` (the client's CRM, and whether a push was tested).

### Unit cost behind the bundle

[not verified] Copied from `testing/facts-round3.md`. Every rate is a HighLevel rate seen in search-result text on 2026-11-15, in US dollars. None was read from an official page or from Ray's own bill.

Two assumptions sit inside the arithmetic:

1. **Token cost.** The language model is taken at one US cent a minute in the planning case. No per-minute figure exists for it.
2. **Exchange rate.** 1 USD = 1.40 CAD. No exchange rate was looked up.

Cost of one AI call minute, in US dollars:

| Part | Low case | Planning case | Note |
|---|---|---|---|
| Voice Engine | 0.045 | 0.045 | |
| Speech | 0.015 | 0.035 | The premium voice at 0.170 is excluded and is not used on this plan. |
| Language model tokens | 0.002 | 0.010 | Assumption 1. |
| Phone, inbound | 0.01165 | 0.0129 | The two figures seen. |
| Transcription | 0 | 0.024 | In the planning case in case it is charged on Voice AI calls. |
| Recording | 0 | 0 | Off by default in the offer. |
| Total, USD | 0.0737 | 0.1269 | |
| Total, CAD at 1.40 | 0.103 | 0.178 | Assumption 2. |

The bundle, planning case:

| Item | Sum | USD | CAD at 1.40 |
|---|---|---|---|
| 250 minutes | 250 x 0.1269 | 31.73 | 44.42 |
| Local number | 1 x 1.15 | 1.15 | 1.61 |
| 500 text segments | 500 x (0.00747 + 0.005 carrier estimate) | 6.24 | 8.73 |
| Bundle cost | | 39.12 | 54.76 |
| Share of $300 CAD | 54.76 / 300 | | 18.3% |

- The same bundle at the standard price of $400 a month is 13.7%.
- An extra minute at $0.30 CAD against a planning cost of 0.178 CAD leaves 0.122 CAD, 41% of the price.
- An extra agent line at $150: 125 minutes, a number and 250 text segments cost 20.13 USD, 28.18 CAD, 18.8% of $150.
- What would break it: a real all-in minute above 0.142 USD, the premium voice, two phone legs billed on every call, the Canadian dollar past about 1.53, or text use far above 500 segments.

Recheck margin against a real invoice after the first month.

### Promise tests

Run in NL Demo first, then in each client account before go-live. Tick a line only when seen on screen or heard on a call.

- [ ] Bundle: a test month with fewer than 250 minutes produces an invoice for the monthly price only.
- [ ] Extra minutes: a test month past the allowance bills each extra minute at $0.30 CAD.
- [ ] Rounding: a test call of under one minute counts as one minute. The count is zero after the billing date.
- [ ] Invoice: the test invoice, or the statement sent with it, shows minutes included, minutes used and extra minutes billed.
- [ ] Cap: set a low cap in NL Demo, use it up, and confirm the AI stops, the alert arrives by text and email, and the phone rings through as before. Repeat with the cap at zero.
- [ ] Team pool: on a test account with two lines, calls on either line count against one allowance of 375 minutes.
- [ ] Demo line: dial it from an outside phone. It answers, says it is an AI, and books a sample appointment.
- [ ] Language: for each language in `nl_languages`, the client made a test call on their own line and signed off.
- [ ] No contact: search the agency account and the Ray Homes account for a sample contact that exists only in the test client account. It is not there.
- [ ] Staff access: a staff user with no open set-up or fix cannot open the test client account. The access log shows who opened it, when and why.
- [ ] Recording off: make a test call in a new account. No audio file exists afterwards, and the transcript and summary still arrive.
- [ ] Recording on: switch it on in NL Demo. The AI says the recording line at the start of the call.
- [ ] Summary: after a test call, the summary arrives by text and by email.
- [ ] CRM push: for each of the four CRMs, a test record arrives in that CRM after a real test call.
- [ ] Urgent call: ask for a person on a test call. The AI offers a callback and the text alert arrives at once.
- [ ] Forwarding when unanswered: let the client's phone ring out. The AI answers. Answer the phone on the next call. The AI does not.
- [ ] Forwarding when the phone is off: switch the phone off and call. The AI answers.
- [ ] Cancel: run the offboarding procedure on a test account. The export arrives, the contacts and transcripts are gone from the account, and forwarding is off.
- [ ] Inbound only: no outbound AI call step is switched on in the account.
- [ ] Waitlist form and US list form: submit each with the box unticked. No message is sent.

## Next step

Diana works through section 1 in the live account and replaces each `[verify in HighLevel]` with yes, no, or how. Section 13 comes next: every promise there is checked before the first founding client is sold on it.
