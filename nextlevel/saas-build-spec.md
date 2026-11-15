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
| Lead | Quiz submitted, or audit call logged | Audit email sent, or call booked |
| Audit sent | Missed-call audit email sent | Call booked |
| Call booked | 15-minute call on the calendar | Call held |
| Won | Payment received | Intake form sent |
| Onboarding | Intake form sent | Step 9 of the checklist done |
| Live | Go-live confirmed | Stays here |
| At risk | Any churn signal in section 11 | Back to Live, or cancelled |

**Calendars**
- "Next Level 15-minute call". Ray first. Nadiya added later. Round robin when both are on. [verify in HighLevel]
- "Onboarding call". Diana or Ray.
- "Day 3 check" and "Day 14 check". Short calls or a logged message.

**Follow-up workflows**
- One per problem: missed calls, reviews, dead database, ads. Three emails each (copy in `sales/follow-up-emails.md`).
- Each stops the moment a call is booked.
- Each sends only to contacts who ticked the consent box.
- Booked-call reminder workflow.
- No-show workflow: one message, then a task for the closer.
- Won workflow: sends the intake form, creates the onboarding tasks, moves the stage.

**The community**
- Free "AI for Agents" group on HighLevel Communities. [verify in HighLevel]
- Joining the community is not consent to marketing email. Keep the two separate.

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
| NL 01 | Appointment reminders | Confirmation and reminders. | Answer |
| NL 02 | Review request at closing | Triggered when the stage moves to Closed. | Reviews |
| NL 02 | Review request at day 30 | Second request 30 days after closing, only if no review yet. | Reviews |
| NL 02 | Review reply draft | New review arrives: AI drafts a reply for the client to approve. Never auto-posts. [verify in HighLevel] | Reviews |
| NL 03 | Reactivation campaign | Messages past contacts who have a valid consent basis. Replies go to the client. | Nurture |
| NL 03 | Hand-raiser follow-up | Anyone who replies with interest gets a task and a booking link. | Nurture |
| NL 03 | Past-client touches | Scheduled check-ins for past clients. | Nurture |
| NL 00 | Unsubscribe and STOP handling | Applies `nl-do-not-contact`, stops every workflow. | All |
| NL 00 | Monthly report | Builds and sends the client report (below). | All |

All workflows ship switched off. They are turned on during onboarding, one at a time.

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
| NL Answer | Next Level Answer | [Ray to set after 60 days of proof] | Proposal in `offer.md` |
| NL Reviews | Next Level Reviews | [Ray to set after 60 days of proof] | Proposal in `offer.md` |
| NL Nurture | Next Level Nurture | [Ray to set after 60 days of proof] | Proposal in `offer.md` |
| NL Ads | Next Level Ads | [Ray to set after 60 days of proof] | Proposal in `offer.md` |
| NL Complete | Next Level Complete | [Ray to set after 60 days of proof] | Proposal in `offer.md` |

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
- For the Founding 10: decide whether usage is included or rebilled. [Ray to set: usage included or rebilled for the Founding 10]
- Tell every client in writing, before they pay, what is rebilled and how.

## 8. The 9-step onboarding checklist

PROPOSED, Ray to approve. Goal: live in 7 days.

1. **Payment and welcome.** Payment received. Welcome email sent with the intake form and the onboarding call link. Stage moves to Won, then Onboarding.
2. **Intake form back.** Business details, hours, areas, top questions, who gets hand-offs, calendar, number to forward. The 7 days start here.
3. **Sub-account cloned.** New sub-account created from the Next Level snapshot. Client user added.
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

Also watch, from the sales side: quiz completions, audits sent, calls booked, calls held, Won.

No targets are set here beyond the ones in the Blueprint: 10 paying agents by end of January, $3,000 monthly recurring revenue from the Founding 10, churn under 5%.

## Next step

Diana works through section 1 in the live account and replaces each `[verify in HighLevel]` with yes, no, or how.
