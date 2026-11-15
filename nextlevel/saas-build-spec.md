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
- Dari and other languages: [verify in HighLevel]

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
7. Run the promise tests in section 13 before any client account goes live, and again after every snapshot change. (Set 2026-11-15 after the persona test; Ray to confirm.)

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

Gate reminder: the business edition is designed here and nothing more. No business sub-account is created for a paying or free client until real estate has paying clients and a repeatable onboarding. Mortgage brokers first.

## 5. Listing data (agent edition only)

- Repliers feeds listing status so the agent can answer "is this home still available?"
- Whether one Repliers licence can serve client sub-accounts, and in which boards: [Ray to confirm: Repliers licence terms for client accounts]
- Until confirmed, the voice agent takes a message on listing questions and books a call.

## 6. SaaS plans mapped to the product ladder

Create these in the SaaS configurator. How many plans the configurator allows: [verify in HighLevel]

| SaaS plan in HighLevel | Product | Price | Status |
|---|---|---|---|
| NL Answer Founding | Next Level Answer, Founding 10 | $300 a month | Ready to create once Stripe is verified. Cap at 10 sales. |
| NL Answer | Next Level Answer | $500 setup + $400 a month | Approved by Ray, 2026-11-15 |
| NL Reviews | Next Level Reviews | $250 setup + $150 a month | Approved by Ray, 2026-11-15 |
| NL Nurture | Next Level Nurture | $500 setup + $250 a month | Approved by Ray, 2026-11-15 |
| NL Ads | Next Level Ads | $500 setup + $750 a month, with ad spend on the client's own card | Approved by Ray, 2026-11-15 |
| NL Complete | Next Level Complete | $1,500 setup + $1,500 a month | Approved by Ray, 2026-11-15 |

All prices in Canadian dollars. Product names and prices: Approved by Ray, 2026-11-15. Rungs 2 to 5 are created now and released one at a time (see `offer.md` section 8).

- Each plan switches on only the features that rung needs, so a Reviews client does not see the voice agent. [verify in HighLevel]
- Setup fees: whether the configurator can charge a one-time fee with a plan, or needs a separate Stripe product: [verify in HighLevel]
- A hard cap of 10 on the founding plan may need to be done by hand (hide the checkout after sale 10). [verify in HighLevel]

## 7. Rebilling

| Usage | Rebilled to the client | Markup |
|---|---|---|
| Phone (minutes, numbers) | Yes | markup: [Ray to set] |
| SMS | Yes | markup: [Ray to set] |
| Email | Yes | markup: [Ray to set] |
| AI usage (voice minutes, conversation AI, content AI) | Yes | markup: [Ray to set] |

- Rebilling needs Stripe connected and a card on file in each sub-account. Blocked until Stripe verification.
- Each sub-account has a prepaid balance that refills. Set the starting amount and refill amount. [Ray to set: starting balance and refill amount] [verify in HighLevel]
- For the Founding 10: usage is rebilled at cost with no markup, up to a monthly cap the client sets. (Set 2026-11-15 after the persona test; Ray to confirm.) The markup in the table above applies after the Founding 10. Build requirements are in section 13. The rate per minute as a number, and whether the margin at $300 is acceptable: [Ray to add: usage rate per minute] [Ray to confirm: margin at $300 with usage at cost]
- Tell every client in writing, before they pay, what is rebilled and how.

## 8. The 9-step onboarding checklist

PROPOSED, Ray to approve. Goal: live in 7 days. The live-in-7-days commitment itself is approved by Ray, 2026-11-15: live within 7 days of the client supplying everything needed, or the first month is not charged (once per client, first month only, not for carrier or registration delays). Feedback calls at day 14 and day 30 are also approved for founders.

1. **Payment and welcome.** Payment received. Welcome email sent with the intake form and the onboarding call link. Stage moves to Won, then Onboarding. Added from the course notes, 2026-11-15: the welcome email also carries one short welcome video (what happens in the 7 days, what the form asks, how to reach us). Ray chose an AI-made video, 2026-11-15. The script is in `onboarding/welcome-video-script.md`, DRAFT for Ray's approval. PROPOSED, Ray to approve: the client agreement is accepted before work starts [Ray to confirm with counsel: the client agreement].
2. **Intake form back.** Business details, hours, areas, top questions, who gets hand-offs, calendar, number to forward. The 7 days start here.
3. **Sub-account cloned.** New sub-account created from the Next Level snapshot. Client user added. The client user sees the features of the rung they bought and nothing half-built. They are told in writing what else exists and when it opens. The client connects their own Google, Facebook and Instagram accounts while logged in as themselves. Next Level never asks for or stores a client's passwords. (Added from the course notes, 2026-11-15.)
4. **Custom values filled.** Every `nl_` value entered and read back.
5. **Phone ready.** Number bought or forwarding set from the client's current number. Messaging registration filed if required.
6. **Calendar connected.** Client's calendar linked. A test booking made and removed.
7. **Voice agent set.** Prompt slots filled. AI disclosure line and recording line confirmed for the client's province or state. [Ray to confirm with counsel] Internal test calls done.
8. **Client test and sign-off.** The client calls their own line, hears the agent, asks for changes, approves.
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

Set 2026-11-15 after the persona test; Ray to confirm. The round 2 offer (`testing/offer-pitch-v2.md`) is the working offer. The assistant set these terms after the persona test, under Ray's instruction to fix the offer. Ray has not approved them yet. Each term is a promise made to a buyer, so each one is a build requirement here. Full wording: `offer.md` section 6.

A promise marked `[verify in HighLevel]` depends on the platform. If the check comes back "no", the promise is kept by hand with a written procedure, or the wording in `offer.md` changes before anyone is sold on it. No client goes live on a promise that has not been checked.

| # | Promise | What the build must do | Check |
|---|---|---|---|
| 1 | Usage at cost, no markup, for founders | Rebilling for the NL Answer Founding plan is set to pass usage through with no markup on phone, text and AI minutes. The client can see their usage in their own account. | [verify in HighLevel: rebilling with no markup on one plan while other plans carry a markup] |
| 2 | Client-set monthly cap, with a stop and an alert | A per-account spending cap, entered at intake and stored as `nl_usage_cap`. When usage reaches the cap, the AI stops taking calls, the client is alerted by text and email, and calls ring through to the client's own phone or voicemail as they did before. | [verify in HighLevel: per-account spending cap and stop] |
| 3 | Ray's own bill shown on the call | The usage and billing view for the Ray Homes account can be shown on a shared screen with no caller details in view. | [verify in HighLevel] |
| 4 | Dial the live system on the call | A demo line that is always on, answers as an AI, and holds no real contacts. It is tested before every sales call. | [Ray to add: demo line number] |
| 5 | English at launch, other languages tested on the client's line | Onboarding step 7 gains a language test: the client calls their own line in each language their callers use and signs off, or the account does not go live and no charge is made. `nl_languages` lists only languages that passed. | [verify in HighLevel: languages the voice agent supports] |
| 6 | No contact with a client's callers | No agency-level workflow, campaign or list reads a client sub-account's contacts. Nothing is copied from a client account into the Next Level or Ray Homes accounts. The clause is in the client agreement. | [Ray to confirm with counsel: the client agreement] |
| 7 | The transcript stays in the client's account. Staff read it only during setup or a fix | Staff reach a client account through a named user with the lowest role that does the job. Access is opened for setup or for a fix the client asked for, then removed. Every access is logged with the date and the reason. | [verify in HighLevel: access control for staff, per sub-account, with a log] |
| 8 | Transcripts kept only while the client stays | A stated retention rule for transcripts and call summaries in each account, and a way to delete them. | [verify in HighLevel: transcript retention] [Ray to add: where client data is hosted] |
| 9 | Audio recording off by default | Call recording is off in the snapshot and in every new account. Turning it on is the client's choice, made in writing. | [verify in HighLevel: recording off by default] |
| 10 | Recording announced when on | When recording is on, `nl_recording_line` is filled and the AI says it at the start of every call. When recording is off, the line is empty and nothing is recorded. | [Ray to confirm with counsel] |
| 11 | Export and deletion on leaving | An offboarding procedure: export contacts and transcripts to the client, confirm they received the file, delete both from the account, then close the account. | [verify in HighLevel: export and deletion] |
| 12 | Summary by text and by email | The "AI call finished" workflow sends the summary to the client by text and by email after every call. | Test call |
| 13 | Direct CRM push confirmed before payment | A written list of the CRMs with a tested push, kept current. A CRM is on the list only after a test record arrived in it. Anything else gets the text and email summary. | [verify in HighLevel: outbound webhooks or integrations] [Ray to confirm: which CRMs get a direct push] |
| 14 | One-page brokerage summary, first month back if the brokerage says no within 14 days | The one-page summary exists as a file. A refund procedure exists for the first month and is logged on the contact. | [Ray to confirm: the day the 14 days are counted from] |
| 15 | Urgent-call callback and text alert | When a caller asks for a person or the call is urgent, the AI offers a callback, the "Needs a human" workflow texts the client at once, and a task is created. The copy promises a callback and an alert. It does not promise a live transfer, so `nl_transfer_number` is used only where a transfer has been tested. | Test call |
| 16 | Forwarding only when unanswered, including when the phone is off | Forwarding is set as conditional: no answer, busy and unreachable. It is never set to forward every call. | [verify in HighLevel: call forwarding conditions] [verify with the client's carrier] |
| 17 | Forwarding off on the day of cancelling | The offboarding procedure removes forwarding on the cancel date and a test call confirms the client's phone rings as before. | Test call |
| 18 | One subscription, one business line | One sub-account and one number per subscription. Routing to several agents is built only after a team quote is accepted. | [verify in HighLevel: routing one line to several users] [Ray to set: team pricing] |
| 19 | Other businesses after the first 10 agents are live | The waitlist form has a consent box that is not pre-ticked and one question: industry and biggest phone problem. No checkout exists for a non-agent plan until the industry opens. | Form test |
| 20 | Canada first, US confirmed per state | Before a US client is accepted: a number can be bought for their state, text registration can be filed, and the recording and AI disclosure rules are confirmed for that state. | [verify in HighLevel] [Ray to confirm with counsel] [Ray to confirm: which US states] |
| 21 | Registered name and address on the agreement | The agreement and every footer carry the registered business name and address. | [Ray to confirm: business name and mailing address for Next Level] |

New custom values for the snapshot: `nl_usage_cap` (the monthly cap the client chose), `nl_recording_on` (yes or no, default no), `nl_summary_email` and `nl_summary_mobile` (where summaries and alerts go), `nl_crm_name` (the client's CRM, and whether a push was confirmed).

### Promise tests

Run in NL Demo first, then in each client account before go-live. Tick a line only when seen on screen or heard on a call.

- [ ] Usage: the founding plan shows usage at cost with no markup on a test invoice.
- [ ] Cap: set a low cap in NL Demo, use it up, and confirm the AI stops, the alert arrives by text and email, and the phone rings through as before.
- [ ] Demo line: dial it from an outside phone. It answers, says it is an AI, and books a sample appointment.
- [ ] Language: for each language in `nl_languages`, the client made a test call on their own line and signed off.
- [ ] No contact: search the agency account and the Ray Homes account for a sample contact that exists only in the test client account. It is not there.
- [ ] Staff access: a staff user with no open setup or fix cannot open the test client account. The access log shows who opened it, when and why.
- [ ] Transcript retention: the retention setting is as written, and a deleted transcript cannot be opened afterwards.
- [ ] Recording off: make a test call in a new account. No audio file exists afterwards.
- [ ] Recording on: switch it on in NL Demo. The AI says the recording line at the start of the call.
- [ ] Summary: after a test call, the summary arrives by text and by email.
- [ ] CRM push: for each CRM on the list, a test record arrives in that CRM.
- [ ] Urgent call: ask for a person on a test call. The AI offers a callback and the text alert arrives at once.
- [ ] Forwarding when unanswered: let the client's phone ring out. The AI answers. Answer the phone on the next call. The AI does not.
- [ ] Forwarding when the phone is off: switch the phone off and call. The AI answers.
- [ ] Cancel: run the offboarding procedure on a test account. The export arrives, the contacts and transcripts are gone from the account, and forwarding is off.
- [ ] One line: the test account holds one number.
- [ ] Waitlist form: submit it with the box unticked. No message is sent.
- [ ] US state: for a US test, the number, the text registration and the rules check are all recorded before go-live.

## Next step

Diana works through section 1 in the live account and replaces each `[verify in HighLevel]` with yes, no, or how. Section 13 comes next: every promise there is checked before the first founding client is sold on it.
