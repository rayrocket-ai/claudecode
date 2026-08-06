# CRM data dictionary + pipeline specifications — DRAFT v0.2

Plan §6.1: this document is the first deliverable of Phase 1, before code.
It is the contract every agent and workflow follows: exact fields, tags,
stage entry/exit conditions, per-stage owner, and max idle time.

**Status: DRAFT.** v0.2 (2026-08-06) reconciles this document with the
executable version in `hq/rayos/pipelines.py` — the stage tables below and
that module are now the same specification, and a test asserts the stage
counts and that no stage is left ungoverned. It freezes to v1.0 only after the Phase-0 Lofty snapshot
(`hq/PHASE0-RUNBOOK.md` §3) shows which of these fields/pipelines map
natively onto Lofty's model and which live in the Postgres ledger with a
Lofty tag pointing at them. Stage counts follow the agreed targets
(Buyer 16 · Seller 15 · Recruiting 13); the lists below are the working
draft built from the plan's §4.6 lifecycle checklists.

## 1. Identity model

One internal person = one `person_id` in the ledger ↔ one Lofty lead ID.
All emails, phones, WhatsApp/IG handles, Telegram IDs, and VOW accounts map
to that one person (dedup job, Phase 1). A person can carry **multiple
party types simultaneously** (a past buyer can be a current seller lead and
an investor).

`party_type` (multi-valued): `buyer` · `seller` · `landlord` · `tenant` ·
`investor` · `precon_purchaser` · `agent_recruit` · `commercial_inquiry`.

**Recruiting contacts are strictly segregated from consumer leads** —
separate pipeline, separate consent basis, never co-mingled in sends.

## 2. Where each field lives

| Owner | Fields |
|---|---|
| **Lofty** (via CRM adapter) | Contact identity, pipeline + stage, tags, tasks, appointments, notes/activity log, optional email/SMS sends |
| **Postgres ledger** | Consent evidence (source/timestamp/scope/proof — CRTC burden-of-proof), suppression list, work orders, full message log, approvals + audit, KPI ledger, and any field Lofty's model can't hold (Lofty then carries tag `ledger:<field>` as the pointer) |

Rule: the send layer checks the ledger's suppression list itself —
suppression is never delegated to prompts or to Lofty tags alone.

## 3. Contact-level required fields

Phase 1 exit says every lead has **owner, stage, source, consent state,
next action** — those five are non-nullable from intake onward.

| Field | Values / format | Notes |
|---|---|---|
| `source` | enum: vow / calculator / gmail / sms / whatsapp / ig / voice / referral / sign_call / open_house / portal / precon_list / manual | captured at intake, never overwritten |
| `owner` | team member or AI role | routed per roster (plan §2 Team) |
| `consent_state` | none / attested_2026-08-02 / express / implied(+expiry) / withdrawn | ledger holds the evidence row; existing book = owner attestation |
| `next_action` + `next_action_due` | text + timestamp | no lead sits without one; Ops Analyst audits weekly |
| `language` | en / fa-dari | selects script-library variant |
| `timeline` | now / 0–3m / 3–6m / 6–12m / 12m+ | qualification output |
| `budget_band` / `price_band` | ranges | buyer/seller respectively |
| `areas` | list of GTA areas/farms | from Ray's service-area input (§9.1) |
| `financing` | pre_approved(+amount) / pre_qualified / not_started / cash / n-a | buyers/investors |
| `vow_state` | none / invited / registered / verified / active / dormant | Phase 3A behavioural sync |
| `suppression` | boolean + reason + timestamp | ledger-authoritative |

Tag conventions: `pt:<party_type>` (mirrors party types into Lofty),
`ledger:<field>` (field lives in Postgres), `cadence:<program>` (8×8,
33-touch, 12-direct), `mode:<market>` (stamped by the SHIFT state machine
on relevant sends).

## 4. Buyer pipeline (16 stages)

Owner legend: CON = Lead Concierge · BS = Buyer Specialist · TA = Transaction
Assistant. "Max idle" = longest a lead may sit in the stage with no
completed activity before escalation (Telegram alert → Ray/owner). Nurture
stages have a cadence instead of an idle cap.

| # | Stage | Entry | Exit | Owner | Max idle |
|---|---|---|---|---|---|
| 1 | New Lead | intake row created | first contact attempt logged | CON | **2 min** (speed-to-lead) |
| 2 | Contact Attempted | attempt logged, no reply | two-way reply | CON | 1 day (then cadence) |
| 3 | In Qualification | two-way conversation live | intent+timeline+location+budget+financing captured | CON | 2 days |
| 4 | Qualified | qualification complete, timeline ≤12m | consult booked OR moved to Nurture | CON | 3 days |
| 5 | Nurture | not ready (timeline >12m or unresponsive) | re-engagement reply | CON | cadence: 8×8 then 33-touch |
| 6 | Consult Booked | buyer consultation on calendar | consult held | BS | cadence: appointment reminders (48h/24h/2h + next-day follow-up) |
| 7 | Consult Done / BRA | consultation held | BRA signed | BS | 5 days |
| 8 | VOW Active — Searching | BRA signed, VOW registered | first showing requested | BS | 7 days (saved-search alerts running) |
| 9 | Showing Scheduled | showing booked (BrokerBay+Calendar) | showing completed | BS | cadence: appointment reminders |
| 10 | Actively Showing | ≥1 showing done | offer-prep appointment set | BS | 5 days (post-showing follow-up drives next showing or offer-prep — every conversation aims at an appointment) |
| 11 | Offer Prep | offer-prep appointment held | offer submitted (approval-gated) | BS | 2 days |
| 12 | Offer Submitted | offer out, irrevocability running | accepted / rejected / expired | BS | **1 day** + hard deadline monitor |
| 13 | Conditional | offer accepted with conditions | all conditions waived/fulfilled | TA | cadence: `deal_conditional` + per-condition hard monitors |
| 14 | Firm | conditions cleared | closing day | TA | pre-closing checklist cadence |
| 15 | Closed | transaction closed | day-1/week-1/30/90 care done | TA | checklist-driven |
| 16 | Past Client | care sequence done | (permanent) | CON | anniversary yearly + 33-touch |

Rejected/expired offers return to 10; lost/withdrawn leads exit to Nurture
or suppression, never deleted.

**Nurture is a branch, not a step.** It is numbered 5 because that is where
it belongs in the CRM's stage list, but the main sequence runs 4 → 6: a
qualified lead's next step is a booked consultation. Any stage before Firm
may fall back to nurture; re-entry from nurture goes to qualification, not
back into a half-finished showing tour. Enforced in `rayos/pipelines.py`
(`branch_keys`) and tested.
The same branch rule applies to the Seller pipeline's stage 5.

**Pre-con track** (first-class per plan §2, §4.6): runs as a parallel
checklist track on a buyer/investor record from stage 8+ — worksheet
submitted → allocation → **10-day rescission countdown (hard monitor)** →
deposit-schedule monitors → interim occupancy → final closing → assignment
watch. Project facts come only from the KB's project cards (citation rule).

## 5. Seller pipeline (15 stages)

LS = Listing Specialist.

| # | Stage | Entry | Exit | Owner | Max idle |
|---|---|---|---|---|---|
| 1 | New Seller Lead | intake row created | first contact attempt | CON | **2 min** |
| 2 | Contact Attempted | attempt logged | two-way reply | CON | 1 day |
| 3 | In Qualification | conversation live | property+motivation+timeline captured | CON | 2 days |
| 4 | Qualified — CMA Prep | qualification complete | CMA/pre-listing package ready | LS | 3 days |
| 5 | Nurture | not ready to list | re-engagement | CON | cadence |
| 6 | Listing Appt Booked | consultation on calendar | appointment held | LS | cadence: appointment reminders |
| 7 | Appt Done — Proposal Out | consultation held | listing agreement signed / declined | LS | 5 days |
| 8 | Listing Signed | agreement executed | pre-market checklist complete | LS | checklist-driven |
| 9 | Pre-Market Prep | photos/staging/media/campaign in motion | live on MLS | LS | 10 days |
| 10 | Active on Market | listed | offer registered | LS | weekly seller report + showing-agent feedback loop (24h/72h, persists until an explicit no, an offer, or the listing ends) |
| 11 | Offer(s) Received | offer registered | acceptance (approval-gated) | LS | **1 day** + irrevocability monitor (hard) |
| 12 | Conditional | accepted with conditions | conditions cleared | TA | cadence: `deal_conditional` + per-condition hard monitors |
| 13 | Firm | conditions cleared | closing | TA | pre-closing checklist |
| 14 | Closed | transaction closed | care sequence done | TA | checklist-driven |
| 15 | Past Client | care done | (permanent) | CON | anniversary + 33-touch |

Expired/terminated listings exit to Nurture with a `relist-watch` cadence.
Price-adjustment recommendations (from feedback summaries + market mode)
are **recommendation-tier** — Ray approves.

## 6. Recruiting pipeline (13 stages) — eXp agent attraction

Separate consent basis; CASL applies to recruiting too. All cold outreach
here is campaign-approved (Phase 6 — this pipeline stays dormant until then).

| # | Stage | Entry | Exit | Owner | Max idle |
|---|---|---|---|---|---|
| 1 | Prospect Identified | added from research | enrichment done | Ops | 7 days |
| 2 | Researched | production/brokerage profile built | outreach drafted | Ops | 5 days |
| 3 | Outreach Approved | Ray approved campaign + draft | first send | — | 2 days |
| 4 | Outreach Sent | sequence running | reply | Ops | 5 days (sequence cadence specified at Phase 6) |
| 5 | In Conversation | two-way reply | discovery call booked | Ray/Ops | 3 days |
| 6 | Discovery Call Set | call on calendar | call held | Ray | cadence: appointment reminders |
| 7 | Discovery Done | call held | decision path chosen | Ray | 3 days |
| 8 | Nurture | interested, not now | re-engagement | Ops | 30 days |
| 9 | Objections / Considering | active objections | resolved either way | Ray | 7 days |
| 10 | Committed — Paperwork | verbal yes | application sent | Ray | 2 days |
| 11 | Signed | application executed | onboarding started | Ops | 2 days |
| 12 | Onboarding | checklist running | checklist complete | Ops | 7 days |
| 13 | Onboarded — Producing | fully active | (permanent; retention touches) | Ops | 90 days |

## 7. Lease / landlord / tenant & investor-resale

Schema (party types + fields) exists from day one; **workflows turn on after
Phase 4** (plan §3). Until then these leads are qualified by the Concierge
and land in Nurture with the correct party type, so nothing is lost. Their
stage lists get specified in v1.1 of this document when the workflows are
scheduled; the lease lifecycle checklist (§4.6: application → signing →
move-in → renewal-date monitor) already defines the skeleton.

Commercial inquiries: qualified structured intake (property class, size,
use, timeline, financing) → routed to Ray personally; tagged
`pt:commercial_inquiry`; no automated workflow (knowledge-first decision,
plan §2).

## 8. Open questions the Phase-0 snapshot must answer

1. Do Lofty pipelines support 16 stages, per-stage metadata, and two-way
   stage sync via API — or do we hold stage in the ledger and mirror a
   coarser stage set into Lofty?
2. Which contact fields are native vs custom-field slots (limits? types?);
   which of §3 need `ledger:` tags.
3. Webhook event catalogue: which of create/update/stage-change/task/
   activity fire webhooks, payload shape, retry behaviour (drives the
   webhook-first + idempotent-poll design).
4. Smart-plan inventory: what's already running in Lofty that would
   double-send against our cadence engine — retire one side per automation.
5. What the existing 7 active API keys have been writing (key audit),
   so historical data quirks are explainable.
6. Rate limits observed in practice (docs vs reality) → adapter throttle
   settings.
