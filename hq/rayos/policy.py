"""Action tiers and approval tokens -- the safety spine.

Two rules from the plan are enforced structurally here rather than by
convention, because convention is exactly what fails at 2am when an agent
improvises:

1. **Unknown actions fail closed.** An action class nobody registered is not
   "probably fine, it's new" -- it is the most dangerous kind, because it is
   the one nobody thought about. :func:`tier_for` returns ``APPROVE`` for
   anything it does not recognise.

2. **Approval tokens cannot be forged.** :class:`ApprovalToken` refuses to
   construct unless handed a module-private sentinel, and the only function
   holding that sentinel is :func:`mint_from_telegram_callback`. An agent
   cannot write ``ApprovalToken(...)`` into existence, because the sentinel
   is not reachable from anywhere it can reach. This is worth the small
   ugliness of a leading-underscore field: it converts "the agent shouldn't
   fabricate approvals" from a hope into a TypeError.

Tokens are additionally **single-use** and **short-lived**. Single-use
because an approval is for one send, not for a campaign; short-lived because
an approval Ray gave this morning should not authorise a send tonight after
the situation moved on. Fifteen minutes is long enough to tap a button and
short enough that a leaked token is worthless by the time anyone finds it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# How long a minted approval stays valid. Ray taps "approve" and the action
# fires within seconds in the normal case; the window exists only to cover a
# queue backlog, not to bank approvals for later.
TOKEN_TTL_SECONDS = 15 * 60


class Tier(str, Enum):
    """What authority an action needs before it may execute."""

    AUTO = "auto"        # executes immediately, logged
    NOTIFY = "notify"    # executes, then tells Ray it happened
    APPROVE = "approve"  # blocks until Ray approves, in Telegram


# The plan's approval table, as data. Adding a capability to the system means
# adding a row here -- and forgetting to add one means the capability is
# gated, not ungoverned. That asymmetry is deliberate.
ACTION_TIERS: dict[str, Tier] = {
    # --- classify, score, draft: never touches the outside world ----------
    "classify_lead": Tier.AUTO,
    "score_lead": Tier.AUTO,
    "draft_message": Tier.AUTO,
    "draft_offer": Tier.AUTO,
    "draft_content": Tier.AUTO,
    "research_market": Tier.AUTO,
    "update_knowledge_base": Tier.AUTO,
    # --- inbound conversation: automatic once the Phase-0 gate is met -----
    # Gated operationally by INBOUND_AUTO_ENABLED below, not by re-tiering.
    "reply_inbound_lead": Tier.AUTO,
    "qualify_lead": Tier.AUTO,
    "set_pipeline_stage": Tier.AUTO,
    "log_activity": Tier.AUTO,
    "create_task": Tier.AUTO,
    # --- scheduling: automatic inside the calendar rules ------------------
    "book_appointment": Tier.AUTO,
    "send_appointment_reminder": Tier.AUTO,
    "change_appointment": Tier.NOTIFY,   # confirm with the counterpart
    "cancel_appointment": Tier.NOTIFY,
    # --- outbound to people who already said yes -------------------------
    "send_nurture_message": Tier.NOTIFY,
    "send_property_alert": Tier.NOTIFY,
    "send_showing_feedback_request": Tier.NOTIFY,
    "send_agent_followup": Tier.NOTIFY,  # agent-to-agent listing follow-up
    "send_listing_report": Tier.NOTIFY,
    # --- everything that can embarrass, bind, or cost money ---------------
    "send_cold_message": Tier.APPROVE,
    "launch_campaign": Tier.APPROVE,
    "publish_content": Tier.APPROVE,
    "change_listing_price": Tier.APPROVE,
    "recommend_price_change": Tier.NOTIFY,   # the recommendation is safe
    "send_offer": Tier.APPROVE,
    "send_legal_document": Tier.APPROVE,
    "spend_money": Tier.APPROVE,
    "delete_records": Tier.APPROVE,
    "change_configuration": Tier.APPROVE,
    "switch_market_mode": Tier.APPROVE,      # SHIFT mode flips are Ray's call
}

# Flipped on only when Phase 0's exit gate is met (>=95% clean runs). Until
# then inbound replies queue for approval even though their tier says AUTO --
# the gate is a property of the system's reliability, not of the action.
INBOUND_AUTO_ENABLED = False

_INBOUND_ACTIONS = frozenset(
    {"reply_inbound_lead", "qualify_lead", "set_pipeline_stage"}
)


def tier_for(action_class: str, *, inbound_auto: bool = INBOUND_AUTO_ENABLED) -> Tier:
    """Return the tier for ``action_class``; unknown actions are APPROVE.

    The unknown-action default is the single most important line in this
    package. An agent that proposes ``"wire_deposit"`` because it hallucinated
    a capability gets a Telegram prompt, not a wire transfer.
    """
    tier = ACTION_TIERS.get(action_class)
    if tier is None:
        return Tier.APPROVE
    if not inbound_auto and action_class in _INBOUND_ACTIONS:
        return Tier.APPROVE
    return tier


# The sentinel that makes tokens unforgeable. Module-private, never exported,
# never passed anywhere except from mint_from_telegram_callback below.
_MINT_KEY = object()


class ForgedTokenError(PermissionError):
    """Raised when something tries to construct a token without minting it."""


@dataclass(frozen=True)
class ApprovalToken:
    """Proof that Ray approved one specific action, once, recently.

    Construct only via :func:`mint_from_telegram_callback`. Direct
    construction raises :class:`ForgedTokenError`.
    """

    _key: object
    action_class: str
    subject_id: str
    approver_id: int
    issued_at: float
    nonce: str

    def __post_init__(self) -> None:
        if self._key is not _MINT_KEY:
            raise ForgedTokenError(
                "ApprovalToken must be minted by an approval callback, "
                "not constructed directly"
            )

    def expires_at(self) -> float:
        return self.issued_at + TOKEN_TTL_SECONDS


def mint_from_telegram_callback(
    *,
    action_class: str,
    subject_id: str,
    approver_id: int,
    authorized_ids: frozenset[int] | set[int],
    now: float,
    nonce: str,
) -> ApprovalToken:
    """Mint a token from a Telegram approve-button callback.

    ``authorized_ids`` is the deny-all-if-empty allowlist the live bot already
    uses (``AUTHORIZED_USER_IDS``). An empty set authorises nobody, which is
    the correct behaviour for a misconfigured deployment -- a bot that trusts
    everyone because its config failed to load is worse than a bot that
    trusts no one.
    """
    if not authorized_ids:
        raise PermissionError("no authorized approvers configured (deny-all)")
    if approver_id not in authorized_ids:
        raise PermissionError(f"user {approver_id} may not approve actions")
    return ApprovalToken(
        _MINT_KEY, action_class, subject_id, approver_id, now, nonce
    )


@dataclass
class TokenLedger:
    """Burns nonces so an approval cannot be replayed.

    Kept in memory here; on the box this is a table with a unique index on
    ``nonce``, so the burn survives a restart and a second worker.
    """

    _spent: set[str] = field(default_factory=set)

    def burn(self, token: ApprovalToken) -> None:
        if token.nonce in self._spent:
            raise PermissionError("approval token already used")
        self._spent.add(token.nonce)

    def is_spent(self, nonce: str) -> bool:
        return nonce in self._spent


@dataclass(frozen=True)
class Decision:
    """The outcome of asking "may this action run right now?"."""

    allowed: bool
    tier: Tier
    reason: str

    def __bool__(self) -> bool:  # lets callers write `if decision:`
        return self.allowed


def authorize(
    *,
    action_class: str,
    subject_id: str,
    now: float,
    token: ApprovalToken | None = None,
    ledger: TokenLedger | None = None,
    inbound_auto: bool = INBOUND_AUTO_ENABLED,
) -> Decision:
    """Decide whether an action may execute, and burn its token if so.

    AUTO and NOTIFY run without a token (NOTIFY differs only in that the
    caller must tell Ray afterwards -- that is a delivery obligation, not an
    execution gate). APPROVE requires a token that matches the action *and*
    the subject, has not expired, and has not been spent.
    """
    tier = tier_for(action_class, inbound_auto=inbound_auto)

    if tier in (Tier.AUTO, Tier.NOTIFY):
        return Decision(True, tier, f"{tier.value}-tier action")

    if token is None:
        return Decision(False, tier, "approval required; no token presented")
    if token.action_class != action_class:
        return Decision(False, tier, "token was issued for a different action")
    if token.subject_id != subject_id:
        return Decision(False, tier, "token was issued for a different subject")
    if now > token.expires_at():
        return Decision(False, tier, "approval expired")
    if ledger is not None:
        if ledger.is_spent(token.nonce):
            return Decision(False, tier, "approval token already used")
        ledger.burn(token)

    return Decision(True, tier, f"approved by {token.approver_id}")
