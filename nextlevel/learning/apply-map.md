# Apply map: course notes to Next Level

Written 2026-11-15. Source: `course-notes-digest.md`. Every edit made to a Next Level file is marked there with "Added from the course notes, 2026-11-15".

Status words:

- **Already covered**: Next Level had it before the notes were read.
- **Added now**: written into a Next Level file today. Drafts and proposals still need Ray's approval.
- **Conflicts with a decision**: the notes say one thing and Ray decided another on 2026-11-15. Ray's decision stands. See the section below the table.
- **Needs Ray**: a real choice or a fact only Ray or counsel can supply. Nothing was built.

## 1. Lesson by lesson

### Foundations

| Idea in the notes | Where it lands | Status | What changed |
|---|---|---|---|
| An automation is a trigger, then actions, with logic and waits | `saas-build-spec.md` section 3, workflow table | Already covered | Nothing. Also used as a teaching post in `content-additions.md`. |
| Booking example: confirm, wait a day, remind, confirm or reschedule | `saas-build-spec.md` section 3, NL 01 Appointment reminders | Added now | The row now names the confirm reply and the reschedule branch. |
| Works for any local business with appointments | `offer.md` section 1 | Conflicts with a decision | Agents first, others on the waitlist. See 2.3. |
| Quick-win list: reminders, reviews, lead capture and nurture, voice receptionist | `offer.md` section 4, `saas-build-spec.md` section 3 | Already covered | Nothing. |
| Quick-win list: website chat, social DM replies, invoicing, post scheduling | `saas-build-spec.md` section 3, "Parked ideas" | Needs Ray | Listed as parked. Not built, not priced. |
| Two routes to the platform: own white-label or the author's licence | `saas-build-spec.md` section 1 | Conflicts with a decision | Ray's own agency stays. See 2.1. |
| Triggers, actions, logic: the builder parts | `saas-build-spec.md` section 3 | Already covered | Nothing. |
| Settings: re-entry, stop on response, sending windows | `saas-build-spec.md` section 3, "Build and test standard" | Added now | A settings checklist every workflow must pass. |
| Testing: sample contact, manual test skips triggers, enrollment history, execution logs | `saas-build-spec.md` section 3, "Build and test standard" | Added now | A six-step test, including a real trigger test and a STOP test. |
| Review request with a rating first, low ratings kept private | `saas-build-spec.md` section 3, "Review requests: one rule" | Conflicts with a decision | Not built. Every client gets the same public link. See 2.9. |
| Ignore memberships, marketplace, media storage and blogs at first | `saas-build-spec.md` section 1, "Out of scope for version 1" | Added now | Scope note. The planned community is flagged for Ray to decide. |
| The author's background and client count | None | Not used | The notes cite figures; not used. |

### Agency roadmap

| Idea in the notes | Where it lands | Status | What changed |
|---|---|---|---|
| Stage 1 and 2: platform, brand, logo, domain, site, Google profile, phone number, Stripe | `ghl-location-setup.md`, `README.md` build order steps 1 and 3 | Already covered | Nothing. Stripe is still blocked. |
| Stage 3: three sub-accounts (own business, demo, first client) | `saas-build-spec.md` sections 1 and 2a | Added now | The NL Demo sub-account, with made-up contacts, proposed for screen sharing and testing. |
| Stage 3: demo automations and a small portfolio | `README.md` build order step 2 | Already covered | The live demo on Ray Homes is the portfolio. |
| Stage 4: first contact only books a call | `offer.md` section 1, `sales/call-script.md` top | Added now | Written as a rule for every first contact. |
| Discovery call: find the pain | `sales/call-script.md` section 2 | Already covered | Five questions existed. |
| Pain list: slow follow-up, no site chat, weak Google presence, after-hours calls, no CRM | `sales/call-script.md` section 2, "What to listen for" | Added now | A table mapping each pain to a rung, and one after-hours question. |
| Present and try to close on the call | `sales/call-script.md` sections 4 to 7 | Already covered | Nothing. |
| If no close, send a proposal | `sales/call-script.md` section 7, `sales/follow-up-emails.md` "After-call summary" | Added now | A one-page summary email, sent only when the person says yes to it. |
| Invoice and contract; have an AI-drafted contract reviewed | `saas-build-spec.md` section 8 step 1 | Added now | Client agreement accepted before work starts, marked for counsel. |
| Add the client as a user with limited permissions, to upsell hidden features later | `saas-build-spec.md` section 8 step 3 | Conflicts with a decision | Client sees their rung and is told what else exists. See 2.8. |
| Client connects their own Google and social accounts | `saas-build-spec.md` section 8 step 3 | Added now | Written as a rule: no client passwords held by Next Level. |
| Build in the client's sub-account | `saas-build-spec.md` section 8 | Already covered | The snapshot clone replaces per-client building. |
| AI assistant writes the script and every reply | `sales/call-script.md` "Before the call"; section 3 below | Added now | A pre-call brief drafted by the Leads and Booking role. Ray speaks in his own words. See 2.10. |

### What to sell

| Idea in the notes | Where it lands | Status | What changed |
|---|---|---|---|
| Setup fee plus monthly retainer | `offer.md` section 7 | Already covered | Same model, approved by Ray. |
| The author's price ranges | `offer.md` section 7 | Conflicts with a decision | Ray's ladder stands. See 2.2. |
| Speed to lead | `saas-build-spec.md` NL 01 Speed-to-lead | Already covered | The after-hours test case was added to the test standard. |
| Voice AI caller | Next Level Answer | Already covered | Nothing. |
| Appointment reminder | NL 01 Appointment reminders | Added now | Branch detail, as above. |
| Review request | Next Level Reviews | Already covered | Rule added on the rating split. |
| Lead nurture (no price in the notes) | Next Level Nurture | Already covered | Nothing. |
| Website chat, social DM replies | "Parked ideas" | Needs Ray | Could sit inside Answer and Nurture. No decision made. |

### Getting clients

| Idea in the notes | Where it lands | Status | What changed |
|---|---|---|---|
| Order: warm network, then one outbound channel, then inbound and partnerships | `README.md` "How people find Next Level" | Conflicts with a decision | Inbound stays first. See 2.4. |
| Warm network list and the 15 to 20 minute ask | `offer.md` section 1 "Secondary channels"; `content-additions.md` O1 | Added now | Proposed as a secondary channel for agents Ray knows personally. Consent flagged for counsel. |
| Free audit and a short report afterward | `sales/missed-call-audit.md` | Already covered | The missed-call audit is this idea, already drafted. |
| Three warm objections: AI does not apply, no time, you are new | `offer.md` section 11, `sales/call-script.md` section 6 | Added now | Three answers in Ray's words. The notes' answer to "you are new" was not used. See 2.5. |
| Discount the first client for a case study and testimonial | `offer.md` section 6 | Added now | Founders may be asked at day 30 for a review or case study. Their choice, never a condition. |
| Cold calling from a scraped map list | None | Conflicts with a decision | Not used. See 2.4. |
| Call numbers: review the script after a set number of calls | `saas-build-spec.md` section 12, `sales/call-script.md` "Reviewing this script" | Added now | A script review step. The numbers are left for Ray to set. |
| Cold email at volume | None | Conflicts with a decision | Not used. See 2.4. |
| Cold DMs: connection note, then one question | `content-additions.md` O2 and O3 | Needs Ray | Drafted, marked outbound, blocked until counsel confirms a consent basis. |
| Networking: no pitch in the room, sell in the follow-up | `offer.md` section 1; `sales/follow-up-emails.md` "The day after meeting in person"; `content-additions.md` O4 | Added now | A room guide and a next-day email, sent only on a yes. |
| Inbound: profile built around one outcome for one niche | `content-additions.md` I1 | Added now | A profile draft for Ray. |
| Inbound: lead magnet post, comment to get it, collect details, open a conversation | `content-additions.md` I2 to I8; `sales/follow-up-emails.md` "Lead magnet delivery" | Added now | Five lead magnet ideas, post structures and the delivery email. A new weekly measure in `saas-build-spec.md` section 12. |
| Partnerships: referral or white-label, with sweeteners | `offer.md` section 1; `content-additions.md` O6 | Needs Ray | Proposed for after the Founding 10. Terms and referral rules need Ray, counsel and eXp. |

### Free resources

| Idea in the notes | Where it lands | Status | What changed |
|---|---|---|---|
| Sell one standardized product, not custom builds | `offer.md` sections 10 and 12 | Already covered | The master snapshot and "no custom builds" already said this. |
| Five tests of a good product | `offer.md` section 12 | Added now | The ladder scored against the five tests. Answer passes all five. |
| Four steps: pick, standardize, self-serve onboarding, monthly price | `saas-build-spec.md` section 8 | Added now | Welcome video proposed beside the snapshot and intake form. |
| One outcome line: result, then the pain removed | `offer.md` section 3, `sales/call-script.md` section 4 | Added now | One proposed line per rung. No income promise in any of them. |
| One product to a revenue target before a second | `README.md` gate rule | Already covered | The gate rule does this job. The notes cite a figure; not used. |
| Claim the business profile shown by AI assistants | `saas-build-spec.md` "Parked ideas" | Needs Ray | Unverified in the notes. Applies to Ray Homes first. A checklist idea is in `content-additions.md` I7, held until verified. |
| Keep name, phone, address, hours and services identical everywhere | `saas-build-spec.md` "Parked ideas" | Needs Ray | Could be one line on the Reviews intake. |
| Prompt writing: clarity, context, constraints, action verbs, role, format | `saas-build-spec.md` section 3, voice agent prompt slots | Already covered | The slot table is this method. The drills are useful practice for Diana. |
| Ready-made snapshot for another trade | None | Not used | Third-party template. Next Level builds its own on Ray Homes. |
| Licensee-only previews | None | Not used | Titles only. See `open-questions.md`. |

### Results, files and gaps

| Idea in the notes | Where it lands | Status | What changed |
|---|---|---|---|
| Student results and income figures | None | Not used | The notes cite figures; not used. |
| Transcripts and unwatched videos | `open-questions.md` | Needs Ray | Listed as next lessons. |

## 2. Where the notes and Ray's decisions differ

Ray's decisions of 2026-11-15 stand in every case. Each item gives the difference and a recommendation.

**2.1 Platform.** The notes present two routes and lean toward the author's low-cost licence. Ray decided on his own HighLevel agency with SaaS mode. Recommendation: keep Ray's decision. The notes themselves observe that the licence would add templates, not capability. Owning the agency keeps the brand, the client accounts, the billing and the snapshot under Ray's control.

**2.2 Pricing.** The notes suggest higher setup fees and retainers per automation, with no currency stated and no evidence behind the ranges. Ray approved a lower ladder in Canadian dollars and a $300 founding price. Recommendation: keep the approved ladder. Revisit prices only with real numbers from the Founding 10: onboarding hours, usage cost per client, and churn.

**2.3 Niche.** The notes say any local business. Ray decided agents first, with other businesses on a waitlist. Recommendation: keep agents first. The notes name real estate as a workable niche, and the one-outcome, one-niche advice in the inbound lesson supports a narrow start.

**2.4 Outreach.** The notes start with a warm network, add cold calls, cold email or cold DMs, and treat inbound as a later stage. Ray decided inbound content is the main source. Recommendation:
- Keep inbound first.
- Add two secondary channels that fit Ray: agents he knows personally, and rooms where agents gather. Both are proposed in `offer.md` section 1.
- Hold cold DMs until counsel confirms a consent basis.
- Do not use bulk cold email or scraped lists. `offer.md` section 10 already says "never" to scraped lists, and CASL applies to every commercial email and text.
- The existing missed-call audit stays as the one calling tactic, with its legal flags.

**2.5 Proof.** The notes suggest a beginner answer the "you are new" objection by pointing to an established expert behind them. Ray decided the proof is his own business, shown live. Recommendation: keep Ray's proof. Borrowing someone else's standing would be untrue for Next Level and would imply a tie to a third party.

**2.6 Guarantees.** The notes contain no guarantee. Next Level has one proposed commitment (live in 7 days or the first month is not charged) in `offer.md` section 6, still waiting on Ray. Recommendation: no change. Nothing in the notes argues for or against it.

**2.7 Income and results claims.** The notes cite income figures from the author and students. Next Level's rules forbid income claims and invented results. Recommendation: none of it is used. The digest records only that the figures exist.

**2.8 Client permissions.** The notes say to limit a client's access so hidden features can be sold later. Next Level's plan mapping already limits each plan to its rung. Recommendation: keep the limit for a clean, simple login, and tell every client in writing what else exists and when it opens. Hiding features to sell them later does not fit how Ray sells.

**2.9 Review requests.** The notes' example asks for a rating first and sends only high ratings to the public page. Recommendation: do not build it. Ask every client the same way. Review platforms commonly restrict sorting people by rating before the public ask. Marked for verification and counsel in `saas-build-spec.md`.

**2.10 Who writes the words.** The notes hand the script and every reply to an AI sales assistant. Ray decided he sells and closes every call. Recommendation: AI roles draft and prepare (a pre-call brief, a summary email draft), Ray approves and speaks. Nothing reaches a prospect without Ray.

**2.11 How many products.** The notes say one product until it reaches a revenue target. Ray approved five names and prices at once. Recommendation: no real conflict. The gate rule releases one rung at a time, each after it runs on Ray Homes. Sell only Answer until the gate opens Reviews.

## 3. How the one-person company system runs this

The system in `marketing/` has one orchestrator, seven teams of AI roles, an approval loop in Slack and a morning brief. A role is a prompt plus a tool connection. Nothing goes live until Ray approves it. This section maps the notes' workflow onto that system for Next Level.

Today that system is set up for Ray Homes content. Running Next Level through it needs a Next Level knowledge set (voice, offer, rules) and Ray's go-ahead. [Ray to decide: same Slack channel or a separate one for Next Level]

### The notes' six stages, by team

| Stage in the notes | AI team and role | What the role does | What stays human |
|---|---|---|---|
| 1. Platform | Orchestrator | Tracks the checklist in `saas-build-spec.md` section 1 and reports blockers in the morning brief | Ray: Stripe verification, plan check, legal name |
| 2. Brand set-up | Team 2 Creative Studio; Team 6 Search and Website | Drafts page designs and profile copy; later, keeps business details identical across the site and the Google profile | Ray: approves every page; trademark check with counsel |
| 3. Become a builder | Orchestrator, with a builder role | Drafts workflow specs and prompt slots; runs the test standard in NL Demo and reports results | Diana or Ray: clicks in the live account. No AI role changes HighLevel without Ray's approval |
| 4. Sell: content | Team 1 Research and Content | Turns `content-additions.md` and `content/` into the weekly brief, posts, hooks and lead magnets | Ray: records video, approves each piece |
| 4. Sell: design and checks | Team 2 Creative Studio | Compliance check against the rules, design, approval request in Slack | Ray: reacts with a check mark, an x, or changes |
| 4. Sell: publishing and replies | Team 3 Distribution and Community | Schedules approved pieces; drafts replies to comments and lead magnet requests | Ray: sends or approves replies. Direct messages stay draft-only |
| 4. Sell: email | Team 4 Email and Nurture | Loads the approved sequences and one-off emails; checks consent before each send | Ray: approves each email before its workflow is switched on |
| 4. Sell: leads and the call | Team 5 Leads and Booking | Posts new leads, books the 15-minute call, writes the three-line pre-call brief, drafts the after-call summary | Ray: takes every call, runs the demo, states the price, closes |
| 5. Onboard and collect | Team 5 Leads and Booking, with the orchestrator | Sends the intake form, tracks the 9 steps, books the day 3 and day 14 checks | Ray or Diana: the onboarding call, the client test call, sign-off. Counsel: the client agreement |
| 6. Fulfil and retain | Team 7 Analytics Loop | Builds the weekly numbers and the monthly client report from real account data; flags churn signals | Ray: reads the report before it sends; calls every at-risk client himself |

### The loop, step by step

1. **Monday.** Team 1 reads last week's loop feed and picks topics. Lead magnet posts and the hooks from `content-additions.md` enter here.
2. **Draft.** Team 1 writes. Team 2 checks each piece against the rules: no income claims, no invented numbers, the six track-record facts only, CASL lines present.
3. **Approve.** The approval request goes to Slack. Ray reacts. Nothing moves without his check mark.
4. **Publish.** Team 3 schedules approved pieces.
5. **Capture.** A comment or form asks for a lead magnet. Team 3 drafts the reply. Team 4 sends the delivery email. Marketing follow-up goes only to people who ticked the consent box.
6. **Book.** Team 5 posts the lead and the booking. The pre-call brief appears in the morning brief.
7. **Call.** Ray. This is the one human step in the sales machine.
8. **After the call.** Team 5 drafts the summary email if the person asked for one. Ray approves and sends.
9. **Onboard.** The orchestrator tracks the 9 steps. Diana or Ray does the account work.
10. **Measure.** Sunday, Team 7 counts inquiries by platform, lead magnet requests by post, quiz completions, calls booked, calls held and Won. The count feeds Monday's brief and the script review.

### What always stays human

- Every sales call, the live demo and the price.
- Approval of anything a prospect or client will read or hear.
- Any message to a person who has not asked to hear from Next Level. An AI role may draft it. It is not sent until counsel has confirmed a consent basis and Ray has approved it.
- Changes to a live HighLevel account.
- Contracts, legal checks and anything touching eXp.
- Calls to at-risk clients and the day 14 conversation.
- Money: Stripe, prices, refunds.

### Where the notes' AI assistant method fits

The notes use one AI assistant for niche research, scripts, pricing, proposals, workflow design and contracts. In Ray's system those jobs are split by team, each bound by the knowledge files and the approval rules:

| Job in the notes | Role in Ray's system | Limit |
|---|---|---|
| Niche research | Team 1 Research and Content | Agents only until the gate opens an industry |
| Sales scripts and replies | Team 5 drafts; Ray speaks | No reply is sent without Ray |
| Pricing | None | Prices are approved by Ray and are not generated |
| Proposals | Team 5 drafts the after-call summary | Only the approved price and terms |
| Workflow design | Orchestrator with a builder role | Tested in NL Demo first |
| Contracts | None | Counsel |
