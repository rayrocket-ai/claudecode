# HQ — the orchestrated AI company

*The plan for turning seven scattered agents into one firm, and that firm into a
template you can stamp onto any business.*

---

## 1. Context

The Instagram version of this idea — "I turned Claude into my CEO" — is eight
slides of decorative dashboards. But strip the fluff and its fine print says the
one true thing: **"You approve. Claude executes."** That is buildable, and most
of it already exists in this repository as disconnected branches:

| What exists today | Where | Becomes |
|---|---|---|
| Showings, OREA doc generation, tour routing (Telegram bot) | `master` | **Operations** dept |
| ReelForge — content machine with a working learning loop | `claude/video-editing-workflow-h86ru4` | **Media** dept |
| AdMax — paid-ads campaign agents, with per-campaign learning logs | `claude/admax-paid-ads-agent-*` | **Marketing** dept |
| Phone receptionist — call scripts, dashboard, digest emails | `claude/ai-receptionist-phone-*` | **Sales** dept |
| Follow-ups + transaction checklists | `claude/real-estate-task-agent-*` | **Sales** + **Operations** |
| Mortgage calculators with GHL lead capture | `claude/mortgage-calculator-tool-*` | **Finance** dept (lead-gen face) |
| Deal deadline tracker (web app) | `claude/elegant-cori-*` | **Operations** |

Each of these is a competent *employee*. None of them know the others exist.
There is no shared memory, no shared task list, no one reviewing results, no
mechanism for a lesson learned in one to reach another. **HQ is that missing
layer** — not another agent, but the company the agents work at.

Two proven patterns from the ReelForge build are load-bearing here and get
promoted to company-wide law:

1. **The artifact is the product.** ReelForge's rule was "the EDL is the
   product, the MP4 is a build artifact." Generalized: every unit of work in HQ
   is a **Work Order** — a JSON record of what was asked, who did it, what they
   decided, why, and what happened. Auditable, diffable, learnable-from.
2. **The model classifies; code decides.** ReelForge's learning loop
   (fixed correction vocabulary, promotion at 2 occurrences, provenance on
   every rule) is extracted into a shared engine and given to *every*
   department. `reelforge/core/feedback.py` and `playbook.py` are the seed —
   already written, already tested (349 tests).

---

## 2. The org chart

```
                       YOU (Owner)
                        │  approves via Decision Queue (Telegram, already built)
                        ▼
                 ORCHESTRATOR  ("Chief of Staff")
                 plans · routes · reviews KPIs · escalates · writes the daily brief
        ┌─────────┬─────────┬────┴────┬─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼         ▼
     SALES    MARKETING   MEDIA     OPS      FINANCE   ENGINEERING
      lead       lead      lead     lead       lead       lead
        │         │         │        │          │          │
   ┌────┴───┐ ┌───┴───┐ ┌───┴──┐ ┌───┴────┐ ┌───┴───┐ ┌────┴────┐
   receptionist admax  reelforge showings  mortgage  self-repair
   follow-ups  organic  reels    OREA docs invoices  test-runner
   CRM sync    SEO      vlogs    tours     P&L       dept-builder
               listings shorts   deadlines           (Claude Code)
```

**Honest titles.** The orchestrator is a *Chief of Staff*, not a CEO. You are
the CEO. It plans, routes, reviews, and brings you decisions — it does not own
the company's judgment. This isn't modesty; it's the design that makes the
whole thing safe to run unattended.

**One lead agent per department**, each with:
- its own **playbook** (learned rules, with provenance — the ReelForge pattern)
- its own **memory/** (decisions.jsonl, applied.json, style/domain profile)
- its own **worker roster** (subagents it may spawn for specific tasks)
- its own **KPI contract** (2–4 numbers it must report, defined in config)
- its own **feedback vocabulary** (what corrections mean in its domain)

**Workers are disposable; leads are durable.** A worker is a subagent spawned
for one work order and discarded — its context never bloats. The lead persists
across runs through its memory directory, exactly as ReelForge's playbook
persists between renders. This mirrors the editor/producer split that worked:
disposable analysis context, durable taste.

---

## 3. The platform primitives (what HQ actually is)

Six pieces of infrastructure. Everything else is configuration.

### 3.1 Work Orders — the company's EDL

```jsonc
{
  "id": "wo-2026-0812-0143",
  "dept": "sales",
  "title": "Follow up: 12 leads gone quiet 7+ days",
  "origin": "orchestrator/weekly-review",     // or "owner", or another dept
  "tier": "notify",                            // autonomy tier, see 3.3
  "state": "done",                             // queued → running → review → done/failed
  "plan": ["pull quiet leads from GHL", "draft per-lead message", "queue for send window"],
  "decisions": [{ "what": "skipped lead #88", "why": "active offer, contact is agent-to-agent" }],
  "result": { "sent": 11, "skipped": 1, "replies_by": "2026-08-15" },
  "cost": { "tokens": 48210, "dollars": 0.71, "minutes": 4 },
  "review": { "qc": "pass", "notes": [] }
}
```

Every action any agent takes lives inside a work order. This is what makes the
company *learnable*: `/hq-feedback` diffs what was proposed against what you
kept, exactly as ReelForge diffs EDLs. It is also what makes the IG post's
"Results" slide real instead of decorative — the KPI ledger is an aggregation
over work orders, not a screenshot.

### 3.2 The bus — boring on purpose

A SQLite queue plus the systemd/watcher pattern already proven in ReelForge.
No Kafka, no Redis, no message broker. Triggers:

- **cron** — the orchestrator's standup (daily), review (weekly)
- **watchers** — inbox events (a file lands, an email arrives, a webhook fires)
- **the owner** — you say something in Telegram; it becomes a work order
- **cross-dept** — a work order's result spawns another (`media` finishes 3
  reels → `marketing` gets a "distribute" order)

Same discipline as ReelForge's watcher: `nice`-throttled, settle-checked,
crash-isolated per item, atomic writes.

### 3.3 Autonomy tiers — the Decision Queue

The load-bearing safety design. Every action class in every department is
assigned one of three tiers **in config, not in prompts**:

| Tier | Meaning | Examples |
|---|---|---|
| `auto` | Execute, log it | render a reel, update the deadline tracker, draft a doc |
| `notify` | Execute, tell you after | send follow-up to an existing lead, post organic content |
| `approve` | Queue and wait for you | anything client-facing and new, anything ≥ $X spend, anything legal/contractual, ad budget changes |

The approval surface is **the Telegram bot you already have** — auth,
keyboards, and handlers exist on `master`. A pending decision arrives as a
message with Approve / Reject / Edit buttons. This is the "Decision Center"
slide, real, and it costs almost nothing to build because it's a new handler in
an existing bot.

Hard rules that no tier config can override, enforced in code:
- Nothing signs anything. Agents draft; you sign (RECO/TRREB reality).
- No new payment destination without `approve`.
- Cumulative spend per dept per day is capped in config; hitting the cap
  freezes the dept's `auto` tier to `approve` until you reset it.
- CASL: no cold outreach to anyone without documented consent status in the CRM.

### 3.4 Shared memory — three scopes

```
hq/memory/
├── company/          # facts every dept reads: who you are, brand voice,
│   ├── profile.md    #   territory, pricing, non-negotiables
│   └── glossary.md   # entities: your team, key clients, vendors
├── sales/            # per-dept: playbook.md, decisions.jsonl, applied.json,
├── media/            #   provenance.json — the exact ReelForge memory layout,
├── ...               #   one directory per department
└── ledger/           # KPI time series + work-order archive (append-only)
```

The feedback engine is `reelforge/core/feedback.py` extracted to
`hq/core/feedback.py` with one change: the correction vocabulary
(`ADJUSTMENTS`) loads from each department's config instead of being hardcoded.
The mechanics — fixed vocabulary, threshold of 2, `applied.json` preventing
recompounding, provenance surviving rewrites, convergence when you contradict
yourself — are already written and tested. **Do not rebuild them.**

### 3.5 The KPI ledger and the daily brief

Each lead reports its KPI contract into the ledger after every run. The
orchestrator's daily standup produces a **brief** — one Telegram message:

> *Yesterday: 11 follow-ups sent (2 replies), 3 reels rendered (1 awaiting your
> review), showing at 142 Main confirmed for 2pm, ad spend $41/$60 cap.
> Waiting on you: 2 approvals. Flag: mortgage-calc leads down 40% w/w —
> Marketing has a work order open to investigate.*

Weekly, the orchestrator reviews the ledger against targets and *opens work
orders* to close gaps. That is the entire "AI CEO decision process" from the IG
post, implemented as: read numbers → compare to config targets → create work
orders → escalate what needs you.

### 3.6 QC — every department verifies before it reports

ReelForge's QC loop generalizes as a *pattern*: each dept defines checks
(model classifies, code decides) that run on a work order's output before it
can reach `done`. Media already has render QC. Sales gets message-lint (no
unapproved claims, consent status present, correct name — embarrassment
checks). Ops gets date/address cross-validation against the source document.
Failures repair-and-retry up to N times, then escalate — never silently ship.

---

## 4. Real-estate department contracts (v1)

| Dept | Workers (existing code) | KPI contract | Tier defaults |
|---|---|---|---|
| **Sales** | receptionist (phone branch), follow-ups (task-agent branch), GHL sync | leads contacted, response rate, appointments booked | outreach `notify`, new-contact `approve` |
| **Marketing** | AdMax campaigns (admax branch), calculator lead magnets (mortgage branch) | cost/lead, spend vs cap, lead volume | budget changes `approve`, creative rotation `notify` |
| **Media** | ReelForge — reels, vlogs, feedback loop (complete) | clips produced, published, avg retention (when analytics land) | render `auto`, publish `notify` |
| **Operations** | showings/tours/docs (master), deadline tracker (cori branch) | showings handled, docs drafted, deadlines at risk | drafts `auto`, anything sent to a client `approve` |
| **Finance** | calculators, invoice drafts, weekly P&L from the ledger | pipeline value, commission forecast, spend | reports `auto`, any payment `approve` |
| **Engineering** | Claude Code itself, gated by the test suite | uptime, test pass rate, incidents fixed | code changes `notify` + tests must pass; deploys `approve` |

Engineering deserves a note: **the self-improving part is real but bounded.**
Its lead is a Claude Code session with a standing brief: watch the error logs,
fix what breaks, extend what a work order asks for — every change on a branch,
gated by the test suite, deployed only through `approve`. The company improves
itself the way ReelForge was built: with tests and a human on the merge button.

---

## 5. The franchise model — duplicating to other businesses

The discipline that makes this portable: **departments are templates; a
business is a config file.** Nothing business-specific is allowed inside
`hq/core/` — it lives in `company.toml` and dept configs, enforced the same way
ReelForge keeps editorial rules out of prompts.

```
hq/
├── core/                 # the platform: work orders, queue, tiers, feedback,
│                         #   ledger, brief-writer. Business-agnostic. Tested.
├── departments/          # TEMPLATES — lead.md, workers/, default playbook,
│   ├── sales/            #   feedback vocabulary, KPI definitions, QC checks
│   ├── marketing/  media/  operations/  finance/  engineering/
├── companies/
│   ├── ray-realestate/   # company.toml + memory/ + connector secrets
│   └── <next-business>/  # a NEW BUSINESS is: this directory
└── PLAN.md
```

`company.toml` declares: business profile, which departments are enabled,
KPI targets, autonomy-tier overrides, spend caps, connectors (GHL, Telegram
chat id, BrokerBay creds…). Spinning up a plumbing company, an e-commerce
brand, or a client's agency = new company directory, edit the toml, seed
`company/profile.md`, connect its accounts. The playbooks start at template
defaults and **diverge through use** — each business learns its own taste via
the same feedback engine. That divergence-through-feedback *is* the product if
you ever sell this: the template is generic, the learned memory is the moat.

One Hetzner box runs several companies (separate memory roots, shared engine) —
the CCX23 is more than enough until render volume says otherwise.

---

## 6. What the IG post gets wrong, so we don't build it

- **The dashboard is not the product.** Their slides lead with revenue
  screenshots; the real work is the queue, the tiers, and the memory. The
  dashboard is a read-only view over the ledger, built near-last.
- **"AI CEO" inverts the safety model.** The approval queue exists precisely
  because the human is the CEO. Ours says so in the architecture, not just the
  fine print.
- **"One AI" is wrong.** One *orchestrator*, many bounded agents with separate
  memories, budgets, and tiers. A single agent with god-context degrades and
  can't be debugged; a firm of small ones with work orders can.
- **No learning story.** Their loop is "measure → improve → repeat" with no
  mechanism. Ours is the tested ReelForge engine: say it twice, it becomes a
  rule, with the quote attached.

---

## 7. Build order

Each phase ends with something running on the Hetzner box.

| # | Phase | Ships | Builds on |
|---|---|---|---|
| **0** | **Consolidate** — merge the branch agents into `hq/departments/*/workers/` (code moves, no rewrites); inventory what each actually does | one repo, one map | all branches |
| **1** | **Platform core** — work orders, SQLite queue, tier engine, `hq/core/feedback.py` extracted from ReelForge (vocabulary from config) | `hq` CLI: create/list/run work orders | reelforge core, tests |
| **2** | **Decision Queue in Telegram** — approve/reject/edit handlers, spend caps, the hard rules | phone-based approvals | existing bot on `master` |
| **3** | **Two departments live** — Operations (existing bot as workers) + Media (ReelForge as-is); leads with playbooks + KPI contracts | real work flowing through work orders | master + reelforge |
| **4** | **Orchestrator v1** — daily standup brief, routing, weekly review that opens work orders from KPI gaps | the daily Telegram brief | 1–3 |
| **5** | **Sales + Marketing + Finance** — fold in receptionist, follow-ups, AdMax, calculators; CASL/consent checks in Sales QC | 5 depts reporting | branches |
| **6** | **Engineering dept** — error-log watcher, fix-on-branch, test-gated, `approve`-gated deploy | the self-improving loop, bounded | CI + tests |
| **7** | **Status page** — read-only ledger/queue view on the tailnet (absorbs ReelForge phase 9; one dashboard, not two) | see the company from your phone | 4 |
| **8** | **Templatize** — `company.toml`, `hq new-company`, second-business dry run with a fake profile | duplicatable | everything |

ReelForge's remaining phases fold in rather than running parallel: its LibreChat
front end becomes HQ's front end (phase 7 here), its `/reel-bakeoff` becomes a
Media-dept QC option, and Open-Generative-AI lands later as a Media worker.

**Sequencing logic:** 0–2 is the spine and is mostly plumbing around code that
exists. 3–4 makes it feel alive (the daily brief is the moment this becomes
"a company" rather than scripts). 5–6 completes the org. 7–8 makes it a product.

---

## 8. Verification

- **Platform (CI, no server):** work-order state machine, tier enforcement
  (an `approve` action can never execute unapproved — property test), spend-cap
  freeze, feedback engine against the existing 28 ReelForge feedback tests
  re-pointed at config vocabularies.
- **On the box, per phase:** phase 2 — a real approval round-trip from your
  phone; phase 3 — one showing handled and one reel rendered *through work
  orders*, visible in the ledger; phase 4 — five consecutive daily briefs that
  are accurate against the ledger; phase 6 — Engineering fixes a deliberately
  injected failing test on a branch and correctly *waits* for deploy approval;
  phase 8 — second company boots with empty memory and produces its first brief
  with zero code changes.
- **The learning check, company-wide:** tell Sales twice that follow-ups are
  too pushy → Sales playbook changes with the quote attached → next batch is
  measurably softer. Same mechanics as the (passing) ReelForge test.

---

## 9. Open decisions (deliberately deferred)

- **Naming** — "HQ" is a placeholder; pick when the Telegram brief first lands.
- **Where analytics come from** for Media/Marketing KPIs (platform APIs vs
  manual paste) — affects phase 5 scope, not architecture.
- **Multi-tenant isolation level** if this is ever sold to other agents/brokers
  (same box vs box-per-client) — matters at phase 8, not before.
- **ReelForge deployment** — still needs its first real footage run on the
  CCX23 (see `reelforge/docs/SERVER-RUNBOOK.md`); do it during phase 3 since
  Media going live depends on it anyway.
