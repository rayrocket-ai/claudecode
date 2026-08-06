# Ray Real Estate OS

| Document | What it is |
|---|---|
| `PLAN.md` | The approved build plan — strategy, roles, doctrine, phases 0–7 |
| `PHASE0-RUNBOOK.md` | The box-side checklist for week one. Start here on the server. |
| `CRM-DATA-DICTIONARY.md` | The field + pipeline contract (Buyer 16 · Seller 15 · Recruiting 13) |
| `rayos/` | The deterministic core, built and tested off the box |

## What `rayos` is

The plan's rule is **model classifies, code decides**. This package is the
"code decides" half: the parts that must not depend on a language model
agreeing to behave.

```
rayos/policy.py      action tiers + unforgeable, single-use ApprovalToken
rayos/consent.py     the send gate -- CASL consent, suppression, purpose
rayos/workorders.py  the universal artifact and its state machine
rayos/pipelines.py   the three pipelines, with owners and idle limits
rayos/checklists.py  the lifecycle library (8x8, 33-touch, rescission...)
rayos/crm/           adapter interface, in-memory impl, Lofty impl
```

It has **no dependencies**, no database, and no network calls — the CRM
adapter talks through an injected transport. That is deliberate: it means
every safety rule in the system is provable on a laptop, and the Hetzner box
is only ever asked to do the parts that genuinely need it.

```bash
cd hq && python3 -m pytest -q       # 98 tests, no key or network required
```

## What is proven here, and what is not

**Proven by tests:** unknown actions fail closed; approval tokens cannot be
constructed without a Telegram callback, cannot be reused, cannot be moved
to a different action or subject, and expire; suppression outranks every
consent state; expired implied consent stops marketing but not transactional
messages; a duplicate webhook storm creates one lead, not nine; 429s honour
`Retry-After` while 4xx are not retried; no pipeline stage is left without a
governor; the 33-touch program generates exactly thirty-three touches.

**Not proven, and flagged in the code:** Lofty's endpoint paths and payload
field names. `developer.lofty.com` is Cloudflare-blocked from cloud
containers, so every path in `crm/lofty.py::Endpoints` is drafted from the
App Center audit and unverified. They are gathered into one small frozen
dataclass so that Phase 0's snapshot corrects them in a single place —
everything built on top stays untouched.

## Wiring it up on the box

1. Implement `crm.lofty.Transport` over `requests`/`httpx` (one method).
2. Correct `Endpoints` from the Phase-0 snapshot.
3. Back `IdempotencyStore`, `TokenLedger`, `ConsentLedger`, and
   `WorkOrderQueue` with Postgres tables (unique index on the idempotency
   key and on the token nonce — that is what makes the guarantees survive a
   restart).
4. Point the Telegram approve callback at `mint_from_telegram_callback` and
   the Decision Queue at `WorkOrderQueue.blocked()`.
