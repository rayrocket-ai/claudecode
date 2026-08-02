# Ray Growth OS — final build plan

One controlled chief-of-staff system with **three growth engines — Buyer,
Seller, eXp Agent Recruiting** — on one platform: reliable inbound conversion
first, every send disclosed and audited, learning that persists.
Practical build order (supersedes "both equally"): **Buyer first** (VOW + MLS
already operational), **Seller second**, **Recruiting third** (after messaging
+ CRM sync are reliable), **productize last** (60–90 days of proven use). Synthesizes the Codex plan
(reliability-first posture, data architecture, approval policy, CASL) with the
HQ plan (work orders, classify/decide split, the tested learning engine,
Media/ReelForge) and three deep code audits of this repo performed 2026-08-02.

---

## 1. The three systems that exist (verified)

**A. `/opt/realtor-agent` — production, unreliable, becomes THE ENGINE.**
Postgres + durable job queue; Gmail intake, GHL, Boosend (WhatsApp/IG),
Twilio + ElevenLabs voice, PropTx/RESO, BrokerBay, dashboards, OpenClaw/Jarvis
+ Hermes decision layers. Production evidence: 120 leads, 612 messages, 4,768
completed jobs, 132 failed jobs, 106 failed agent turns, **7 of last 9 AI runs
failed**, 368 "exhausted model iterations" errors, 2 showings, 0 offers,
0 learned lessons. *Not yet audited by me — first task of Phase 0.*

**B. This repo (`rayrocket-ai/claudecode`) — a parts warehouse of 4 unrelated
lineages** (verified: several branches share no git history):
- *Realtor Telegram bot* (in daily use at `/opt/realtor-bot`; polling, PTB,
  async SQLite; showings approve/decline is the Decision-Queue blueprint —
  `bot/handlers/showings.py` pattern; auth via `AUTHORIZED_USER_IDS`).
- *Content engine* (`master`!): RSS → idea bank → scripts → teleprompter +
  the receptionist post-call webhook (`dashboard/receptionist.py`).
- *ReelForge* (this branch): complete video editor, 349 tests, learning loop
  proven; never yet run on real footage.
- *Branch assets* (verdicts from audit): task/follow-up loop with cadences +
  escalation (**runs-as-is**, DB-driven, tested); Ontario TRESA checklists
  (**runs-as-is**); deadline reminders + read-only deals dashboard
  (**runs-as-is**); `calc.js` mortgage math (**runs-as-is**, best-tested
  artifact); AdMax strategist prompt + KPI ledger app (**runs-as-is**);
  campaign learning-log schema (**pattern good, never used**).

**C. Third-party brains not in version control:** the ElevenLabs voice agent's
entire prompt/behavior lives in their dashboard; GHL holds live customer data.

**D. The VOW — verified live (by Codex on the box; unverifiable from this
container):** GHL location API 200 · PropTx RESO metadata + live listing query
200 · `homes.rayrealestate.ca` online with registration, email verification,
terms acceptance, broker-consumer acknowledgement, session management,
activity auditing, redistribution/scraping restrictions, licensed
field-display policy. **Zero registered consumers, zero sessions** — built but
unlaunched. Compliance caveat adopted: technical access ≠ contractual
approval; before public launch, audit the portal against the signed
board/PropTx VOW agreement. Rule: **behavioural events and permitted property
references sync to GHL; full MLS listing content stays inside the VOW.**

**Ground truths that shape everything:**
- The mortgage calculators **never reach GHL** — leads go to
  `mailto:info@example.com` (`web/js/config.js` FORM_ENDPOINT empty). Revenue
  leak; two-line fix.
- One Telegram token = one polling process (409 conflicts otherwise); sending
  via HTTP API is safe concurrently → **outbox pattern** for all system→Ray
  messages.
- No migrations anywhere; SQLAlchemy `create_all` won't alter existing tables.
- AdMax has **zero** ads-API code — a human is the data connector (fine; the
  plan keeps it human-in-loop).

## 2. Decisions locked

| Decision | Choice |
|---|---|
| Revenue focus | **Buyer and seller tracks in parallel** (accepted cost: shared foundation first; ~2 weeks longer to first fully-hardened track) |
| AI autonomy | **Inbound-auto from day one of Lead Concierge go-live**, gated on the Phase-0 reliability exit (≥95% clean runs), not a drafting period. Always disclosed as "Ray's AI assistant." Cold outbound + public content stay approval-gated. |
| Canonical app | **`/opt/realtor-agent` = engine** (Postgres = ledger, its queue runs work orders). **Telegram bot = Ray's remote** (approvals, briefs, commands) reading/writing the engine's DB; its overlapping automations retired. Repo assets mount into the engine as workers. |
| CRM | **GoHighLevel = customer source of truth**; Postgres = automation ledger (messages, jobs, runs, consent evidence, approvals, audit). |
| Decision layers | One orchestrator ("chief of staff"). **Hermes/OpenClaw/Jarvis retired as decision-makers** — one command path. |
| Learning | The ReelForge feedback engine (vocabulary → threshold-2 promotion → provenance; 28 passing tests) generalized per role. Directly cures "0 learned lessons." |

## 3. Operating model

```
Lead sources ─→ Unified intake ─→ GHL (customers) + Postgres (ledger)
                                        │
                                  ORCHESTRATOR (chief of staff)
       ┌──────────┬──────────┬──────────┼──────────┬──────────┐
   Lead        Property/   Listing/   Transaction  Operations   Media
   Concierge   Showing     Marketing  Assistant    Analyst      (ReelForge)
       └──────────┴──────────┴─────────┴──────────┴──────────┘
                          APPROVAL & POLICY LAYER (deterministic, fail-closed)
                                        │
                    Gmail · SMS · WhatsApp · Voice · Calendar · BrokerBay · Docs
                                        │
                     TELEGRAM COMMAND CENTER → Ray approves sensitive actions
```

Six roles (Codex's, adopted) + **Media** (ReelForge + AdMax assets feeding the
Listing/Marketing role with reels, listing videos, campaign creative).
Every role: bounded task list, KPI contract, its own playbook + feedback
vocabulary, workers spawned per work order (disposable), lead persists via
memory. **Model classifies; code decides** — state changes (pipeline stage,
bookings, sends) pass deterministic validation; an agent proposing an unknown
action gets dropped-and-reported, never executed.

**Work orders** (from HQ plan) are the universal artifact, stored in the
engine's Postgres: id, role, action_class, tier, state machine
(`queued→claimed→running→review→done|failed|blocked(awaiting_approval)`),
plan/decisions/result, cost (tokens/$), parent chain. The Instagram "results
dashboard" becomes an aggregation over work orders — real numbers only.

**Approval policy** (adopted; enforced structurally — `approve`-tier execution
requires an ApprovalToken mintable only by Ray's Telegram callback):

| Action | Authority |
|---|---|
| Classify/score lead; draft anything; schedule within calendar rules | Automatic |
| Reply to opted-in inbound lead | Automatic (post Phase-0 gate) |
| Change/cancel appointment | Confirm with counterpart |
| Cold email/text | Campaign approval + CASL validation |
| Publish marketing content; price/strategy changes | Ray approves / recommendation-only |
| Draft offer | Allowed |
| Send offer/legal doc; spend money; delete records; config changes | Ray approves (admin for config) |
| Unknown action_class | **approve** (fail-closed) |

## 4. Data architecture

| System | Owns |
|---|---|
| GoHighLevel | Contacts, opportunities, stages, human CRM |
| Postgres (engine) | Work orders, messages, AI runs, consent evidence (source/timestamp/scope/proof — CRTC burden-of-proof), approvals, audit, KPI ledger, outbox |
| Google Calendar | Availability + appointments (authoritative) |
| RESO/PropTx | Property data |
| BrokerBay | Showings |
| Object storage | Docs, reports, media (ReelForge outbox) |
| Telegram | Ray's command center (single-token; outbox drained by the one bot process) |

One internal identity per person, mapping all emails/phones/channel handles;
dedup + sync job (Phase 1). Suppression list checked by the send layer itself,
not by prompts.

## 5. Asset deployment map (what goes where)

| Asset (verdict) | Destination |
|---|---|
| Follow-up cadence engine + Task/TeamMember tables (tested) | Lead Concierge + Ops follow-up core (port to Postgres) |
| TRESA checklists (pure data) | Transaction Assistant task fan-out |
| Deadline reminders engine + `parse_time_of_day` | Transaction Assistant deadline monitor |
| Showings approve/decline handler pattern + keyboards | Telegram Decision Queue blueprint (`dq_` prefix, same split/edit-message retire pattern) |
| `calc.js` + calculators site | Marketing lead magnet — **fix FORM_ENDPOINT → GHL inbound webhook (week 1)** |
| AdMax prompt + KPI dashboard app | Marketing role persona + interim KPI surface |
| Receptionist post-call webhook | Voice intake → engine (auth the `/voice/calls` PII leak first) |
| ElevenLabs agent prompt | **Export into version control** (week 1); add disclosure line |
| ReelForge | Media worker; first real-footage run during Phase 4 |
| Learning-log schema (empty but good) | Superseded by feedback engine; per-campaign logs kept as memory files |

## 6. Roadmap (phases keep Codex's shape; exits are gates, not dates)

**Phase 0 — Stabilize (wk 1).** Read-only audit of `/opt/realtor-agent`
(architecture, the 5-iteration loop bug, the 368 exhausted-iteration errors,
132 failed jobs by type); fix agent loop + unsupported job types; channel-
identity failures; healthchecks on every container; **security sweep**: rotate
all secrets incl. the root password pasted in chat, protect Portainer, auth
`/voice/calls`, purge `content.db` from git; structured error alerts →
Telegram; DB restore test; staging vs prod split; retire double-acting
automations (one BrokerBay poller only). *Exit: ≥95% clean test conversations,
zero unhandled job types — this gate is what turns inbound-auto on later.*

**Phase 1 — GHL backbone & data foundation (wk 2–3).** The audit found the
engine has **no complete GHL sync layer** — this phase is that layer:
contact create/update, opportunity creation, stage sync (two-way), custom-field
mappings, conversation/activity logging, task + appointment sync, webhook
intake from GHL, **idempotency/dedup, consent+suppression sync, retry +
dead-letter handling**. Build the **three pipelines** (Buyer 16 stages, Seller
15, Recruiting 13 — full stage lists + required-field sets per the 2026-08-02
Codex spec, frozen into the GHL data dictionary, §6.1) with owner +
entry/exit + max-idle per stage (no lead sits "new"). Identity dedup (one
person ↔ all channels ↔ one GHL contact ID). **Recruiting contacts strictly
segregated from consumer leads** (CASL applies to recruiting messages too).
Work-order tables + tier engine + ApprovalToken; Telegram Decision Queue +
`/brief` + outbox drainer (additive handlers in the live bot, image-rollback
deploy); import/normalize the 120 leads; port feedback engine to Postgres.
*Exit: every lead has owner, stage, source, consent state, next action;
approval round-trip works on Ray's phone; GHL↔Postgres sync survives a
duplicate-webhook storm without double-creating.*

**§6.1 Next planning artifact (first deliverable of Phase 1, before code):**
the **GHL data dictionary + three pipeline specifications** — exact custom
fields, types, tags, stage entry/exit conditions, per-stage owner and max idle
time. The Codex stage/field lists are the draft; the dictionary freezes them
as the contract every agent and workflow follows.

**Phase 2 — Inbound conversion engine (wk 3–4).** Lead Concierge live across
Gmail/SMS/WhatsApp/voice/web/social forms; ≤2-min disclosed responses;
qualification (intent, timeline, location, budget, financing); GHL stage
placement via validated transitions; scheduling; escalation rules (legal,
financing, complaints); EN + Dari; follow-up sequences on the cadence engine.
Inbound-auto ON (gate met). *Exit: inbound handled end-to-end, zero manual
copying; speed-to-lead measured.*

**Phase 3A — Buyer engine (wk 5–6, leads the parallel pair).** The VOW is the
centerpiece: qualification → **VOW invitation workflow** (registration, email
verification, terms) → authorized RESO search → **behavioural events into GHL**
(registrations, searches, saved searches, favourites, listing views, showing
requests, high-intent repetition, inactivity-triggering-nurture) → saved-search
alerts → tour optimizer + Calendar + BrokerBay → reminders/itineraries →
post-showing feedback → offer approval workflow. Deterministic validation on
all bookings. Pre-launch: VOW-vs-agreement compliance audit (§1.D). *Exit:
inquiry → VOW-registered → completed showing, full audit trail; first real
consumer registrations on the portal.*

**Phase 3B — Seller & listing (wk 5–7, parallel).** Seller intake + listing
appointment booking; listing prep checklist; **Media**: ReelForge deployed
(first real footage), listing videos/reels + AdMax campaign workspace; social/
email approval queue; open-house workflow; weekly seller reports. *Exit: every
active listing has an approved campaign + follow-up plan + measurable report.*

**Phase 4 — Offers & transactions (wk 7–8).** Structured offer intake with
required-field validation; TRESA checklist fan-out; deadline monitors
(irrevocability/conditions/closing) on the reminders engine; document storage;
compliance export. Nothing contractual leaves without explicit authorization.

**Phase 5 — Decision center (wk 8–9).** Morning/evening briefs (deterministic
composer over the ledger); weekly review (KPI deltas → orchestrator proposes
work orders from a fixed vocabulary, code validates); dashboard answering the
five questions (who needs response now / next meetings / stalled / awaiting
approval / failing automations) with real DB values; AI cost + error
reporting; learning loop live for all roles via `/feedback`.

**Phase 6 — Controlled outbound + Recruiting engine (after all above).**
Outbound tiers per the communication policy: *inbound-auto* (live since ph.2);
*outbound nurture auto* only when consent recorded + approved workflow + not
opted out + frequency-capped + stops on reply/booking/opt-out (property
alerts, showing reminders, post-showing follow-up, listing reports,
past-client check-ins); *cold outbound* CASL-complete and campaign-approved:
research → compliance classification → personalized drafts → approval →
rate-limited sends → reply detection → instant suppression → evidence log.
**Recruiting engine** launches here: ideal-agent profile, prospect research
(brokerage/production indicators), personalized recruiting drafts, approved
multistep outreach, discovery-call scheduling, objection/nurture workflows,
onboarding tracking — separate pipeline, separate consent basis.

**Phase 7 — Productize (after 60–90 days of reliable use in Ray's business).**
Config-from-core separation, multi-tenant accounts with isolated credentials
+ data, onboarding wizard, pipeline templates, subscription billing,
tenant domains, RBAC, standardized deploy; pilot with one trusted agent.

## 7. Guardrails (adopted + extended)
No unconstrained agents messaging customers · one CRM · no cold outreach
before consent/suppression works · no AI-invented property facts (listing
claims must cite RESO fields) · no model-driven state changes without
deterministic validation · no offers/legal/ads/spend without approval · no new
dashboards until failure rates are fixed · no productizing early · no second
Telegram poller · unknown actions fail closed · every learned rule carries its
quote and count.

## 8. KPIs (ledger-computed, never decorative)
Median speed-to-lead · contact rate · qualified rate · booking rate · show
rate · offer/listing conversion · closed GCI · source conversion · cost per
qualified appointment · follow-up coverage · human-takeover rate · AI error
rate · approval/edit rate · unsubscribe+complaint rate.

## 9. 90-day target
One engine + one CRM; all inbound channels connected; every lead staged with a
next action; reliable showings and listing campaigns; offer safeguards; real
command-center metrics; documented consent/suppression; **<2% automation
failure**; measurable speed-to-lead, booking and conversion gains; learning
loop demonstrably changing behavior (say it twice → next batch differs).

## 9.1 What we have vs. what is still missing

**In hand (in this plan + this repo + verified):** the full strategy and
phase spec; audited asset map with reuse verdicts; the tested learning engine;
the Telegram approval-surface blueprint; ReelForge complete; draft stage/field
lists for all three pipelines; Codex's live-access verification of
GHL/PropTx/VOW (trusted, not independently verifiable from this container).

**Missing — Ray must supply (blocks the phases marked):**
- ~~Executed VOW/PropTx/board agreement~~ **CONFIRMED HELD by Ray (2026-08-02)
  — signed agreements and approval exist.** Remaining action, Phase 0: locate
  the document(s) on the box or have Ray drop them into the engine's document
  storage, then run the portal-vs-agreement display-rules comparison before
  VOW public launch (ph.3A). The gate is now a checklist item, not a blocker.
- GHL admin access for pipeline/custom-field creation (blocks ph.1)
- Primary GTA service areas; buyer qualification policy; seller
  consultation/CMA process; eXp recruiting value proposition (block the
  respective engines' scripts)
- Approved communication identities (numbers, emails, WhatsApp/IG accounts);
  consent rules + suppression policy sign-off (block ph.2 send-layer config)
- Appointment types + calendar rules; escalation rules (block scheduling)
- Brand voice, English and Dari (blocks message templates)

**Missing — discoverable only on the box (Phase 0 audit):** /opt/realtor-agent
architecture and the root cause of the failure metrics; actual GHL field/
pipeline state; ElevenLabs agent prompt (export to git); VOW codebase state.

## 10. Build logistics
Dev happens against `/opt/realtor-agent` on the box (this container cannot SSH
or reach HuggingFace — Ray runs commands/deploys, Claude designs and debugs
from output; or Claude Code runs directly on the box in tmux, which is the
better loop). This repo's designated branch carries ported assets and docs.
Phase-0 audit output decides whether engine code is fixed in place or
selectively rewritten — evidence first.

## Appendix
ReelForge: complete (phases 0–6+8), 349 tests, commit `0032c06d`; deploy
runbook `reelforge/docs/SERVER-RUNBOOK.md`; first real run scheduled Phase 3B.
Repo topology: `master`=content engine; realtor trunk=`claude/telegram-
showing-bot-qlYMv`; branch merge collisions documented (db/models, config,
bot/main; two different `web/` meanings). Hetzner CCX23 87.99.139.222 — rotate
root password (was pasted in chat). HQ strategic doc: `hq/PLAN.md`.
