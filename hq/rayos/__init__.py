"""Ray Real Estate OS -- the deterministic core.

This package holds the parts of the system that must *not* be decided by a
language model: what tier an action falls into, whether a send is allowed,
which pipeline transitions are legal, and how a work order moves through its
states. The plan's rule is "model classifies, code decides" -- this package
is the "code decides" half.

Everything here is dependency-free and clock-injected, so the rules can be
tested exhaustively without Postgres, without Telegram, and without a CRM
key. The parts that genuinely need the box (the engine's database, the
Telegram token, the Lofty credentials) sit outside and call in.

Layout::

    policy.py      action tiers + unforgeable ApprovalToken (fail-closed)
    consent.py     consent ledger + suppression -- the send gate
    workorders.py  the universal artifact and its state machine
    pipelines.py   Buyer 16 / Seller 15 / Recruiting 13, as data
    checklists.py  lifecycle checklist library (8x8, 33-touch, rescission)
    crm/           adapter interface, in-memory impl, Lofty impl
"""

__version__ = "0.1.0"
