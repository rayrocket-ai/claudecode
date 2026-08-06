"""Consent, suppression, and the send gate.

CASL puts the burden of *proof* on the sender: it is not enough to believe
someone consented, you must be able to show when, how, and to what. So the
ledger stores evidence rows, and the send layer asks this module -- never a
prompt -- whether a message may go out.

The distinction that matters most here is **transactional vs marketing**. A
showing reminder for an appointment the person booked is not a marketing
message, and blocking it because their implied consent lapsed would be a
worse system, not a safer one. A "just checking in, here are three new
listings" message to the same lapsed contact is marketing and must stop.
:class:`Purpose` draws that line explicitly so the rule is inspectable.

Suppression outranks everything, including express consent, because an
unsubscribe is a withdrawal and the timestamp on the older consent record is
irrelevant to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# CASL's implied-consent window for an inquiry is six months; for an existing
# business relationship it is two years from the transaction. Stored as
# explicit expiry timestamps on the record rather than recomputed here, so a
# record always says for itself when it dies.
SIX_MONTHS_SECONDS = 182 * 24 * 3600
TWO_YEARS_SECONDS = 730 * 24 * 3600


class ConsentState(str, Enum):
    NONE = "none"
    ATTESTED = "attested"    # owner attestation for the pre-existing book
    EXPRESS = "express"      # they explicitly opted in; no expiry
    IMPLIED = "implied"      # inquiry or existing relationship; expires
    WITHDRAWN = "withdrawn"


class Purpose(str, Enum):
    """Why we are sending. Determines which consent states suffice."""

    REPLY = "reply"                  # answering something they just sent
    TRANSACTIONAL = "transactional"  # about a thing they are already doing
    NURTURE = "nurture"              # marketing to a warm contact
    COLD = "cold"                    # marketing to someone who never asked


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    VOICE = "voice"


@dataclass(frozen=True)
class ConsentRecord:
    """One evidence row. Everything CRTC would ask for, in one place."""

    person_id: str
    state: ConsentState
    source: str          # "vow_registration", "calculator_form", "verbal_at_showing"
    scope: frozenset[Channel]
    recorded_at: float
    proof: str           # form payload id, recording id, message id, attestation note
    expires_at: float | None = None

    def is_live(self, now: float) -> bool:
        if self.state in (ConsentState.NONE, ConsentState.WITHDRAWN):
            return False
        if self.expires_at is None:
            return True
        return now <= self.expires_at


@dataclass(frozen=True)
class SuppressionEntry:
    person_id: str
    reason: str           # "unsubscribed", "complaint", "manual", "bounced"
    recorded_at: float
    channel: Channel | None = None  # None means every channel


@dataclass(frozen=True)
class SendVerdict:
    allowed: bool
    reason: str

    def __bool__(self) -> bool:
        return self.allowed


@dataclass
class ConsentLedger:
    """In-memory now; a table with an append-only history on the box.

    Records are appended, never edited -- the history *is* the evidence. The
    live record for a person/channel is the most recent one that covers it.
    """

    records: list[ConsentRecord] = field(default_factory=list)
    suppressions: list[SuppressionEntry] = field(default_factory=list)

    # -- writes ---------------------------------------------------------
    def record(self, entry: ConsentRecord) -> None:
        self.records.append(entry)

    def suppress(self, entry: SuppressionEntry) -> None:
        self.suppressions.append(entry)

    # -- reads ----------------------------------------------------------
    def latest_for(self, person_id: str, channel: Channel) -> ConsentRecord | None:
        covering = [
            r for r in self.records
            if r.person_id == person_id and channel in r.scope
        ]
        return max(covering, key=lambda r: r.recorded_at, default=None)

    def is_suppressed(self, person_id: str, channel: Channel) -> SuppressionEntry | None:
        for entry in self.suppressions:
            if entry.person_id != person_id:
                continue
            if entry.channel is None or entry.channel == channel:
                return entry
        return None

    # -- the gate -------------------------------------------------------
    def may_send(
        self,
        *,
        person_id: str,
        channel: Channel,
        purpose: Purpose,
        now: float,
    ) -> SendVerdict:
        """The one function the send layer calls before every outbound message."""
        suppressed = self.is_suppressed(person_id, channel)
        if suppressed is not None:
            # Deliberately absolute. Even a reply to an inbound message stops:
            # if someone unsubscribed and then emailed us, a human answers.
            return SendVerdict(False, f"suppressed ({suppressed.reason})")

        record = self.latest_for(person_id, channel)

        if purpose is Purpose.REPLY:
            # They wrote to us. Answering is not a marketing message, and
            # refusing to answer would be the strange behaviour here.
            return SendVerdict(True, "reply to inbound contact")

        if record is None:
            return SendVerdict(False, "no consent record for this channel")

        if record.state is ConsentState.WITHDRAWN:
            return SendVerdict(False, "consent withdrawn")

        if purpose is Purpose.TRANSACTIONAL:
            # About something they are already doing with us. Any live or
            # lapsed-but-existing relationship carries it; only an explicit
            # withdrawal or suppression stops it, both handled above.
            return SendVerdict(True, "transactional message")

        if not record.is_live(now):
            return SendVerdict(False, f"{record.state.value} consent expired")

        if purpose is Purpose.COLD:
            # Cold means they never asked. By definition no consent record
            # makes a cold send lawful on its own -- it needs the campaign
            # approval path in policy.py as well, which is why this returns
            # the narrower verdict rather than True.
            if record.state is ConsentState.EXPRESS:
                return SendVerdict(True, "express consent on file")
            return SendVerdict(False, "cold send needs express consent")

        return SendVerdict(True, f"{record.state.value} consent live")


def attest_existing_book(
    person_ids: list[str],
    *,
    now: float,
    note: str,
    channels: frozenset[Channel],
) -> list[ConsentRecord]:
    """Record Ray's 2026-08-02 attestation for the pre-existing book.

    An attestation is weaker evidence than a signed form and this does not
    pretend otherwise -- it is stored as its own state so that a later audit
    can tell attested contacts from ones with real capture evidence, and so
    new leads can be held to the higher standard from day one.
    """
    return [
        ConsentRecord(
            person_id=pid,
            state=ConsentState.ATTESTED,
            source="owner_attestation",
            scope=channels,
            recorded_at=now,
            proof=note,
        )
        for pid in person_ids
    ]
