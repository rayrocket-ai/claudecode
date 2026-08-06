"""The CRM adapter interface.

Seven operations, chosen because they are what the engine actually needs --
not a mirror of any vendor's API surface. Anything a particular CRM cannot
hold natively lives in the Postgres ledger, and the contact carries a
``ledger:<field>`` tag pointing at it. That fallback is what keeps this
interface honest: it does not shrink to the weakest CRM's feature set.

``external_key`` deserves a note. Every write carries one, and the adapter
promises that two writes with the same key produce one record. Lofty's
webhooks can and do redeliver, and a duplicate webhook that creates a second
lead is not a cosmetic bug -- it splits a person's history in half and sends
them everything twice.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class CRMError(RuntimeError):
    """Any failure the adapter could not resolve by retrying."""


class PartyType(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    LANDLORD = "landlord"
    TENANT = "tenant"
    INVESTOR = "investor"
    PRECON = "precon_purchaser"
    RECRUIT = "agent_recruit"
    COMMERCIAL = "commercial_inquiry"


@dataclass
class Contact:
    """One person, as the CRM should see them.

    ``person_id`` is ours and authoritative; ``crm_id`` is whatever the
    vendor assigned. Keeping both on the object is what makes the identity
    map work in either direction.
    """

    person_id: str
    first_name: str = ""
    last_name: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    party_types: set[PartyType] = field(default_factory=set)
    source: str = ""
    owner: str = ""
    language: str = "en"
    pipeline: str | None = None
    stage: str | None = None
    tags: set[str] = field(default_factory=set)
    #: Fields the CRM cannot hold natively. Mirrored as `ledger:<key>` tags.
    ledger_fields: dict[str, str] = field(default_factory=dict)
    crm_id: str | None = None

    def merged_tags(self) -> set[str]:
        tags = set(self.tags)
        tags |= {f"pt:{p.value}" for p in self.party_types}
        tags |= {f"ledger:{k}" for k in self.ledger_fields}
        return tags


@dataclass(frozen=True)
class Activity:
    person_id: str
    kind: str          # "email_sent", "call", "showing_completed", "vow_search"
    summary: str
    occurred_at: float
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Task:
    person_id: str
    title: str
    due_at: float
    owner: str
    external_key: str
    hard_deadline: bool = False


@dataclass(frozen=True)
class Appointment:
    person_id: str
    kind: str          # "buyer_consult", "listing_consult", "showing"
    starts_at: float
    ends_at: float
    location: str = ""
    external_key: str = ""


@dataclass(frozen=True)
class WebhookEvent:
    """A normalized inbound event, whatever shape the vendor sent."""

    kind: str          # "contact.created", "contact.updated", "stage.changed", ...
    crm_id: str
    occurred_at: float
    delivery_id: str   # for dedup -- vendors redeliver
    payload: dict = field(default_factory=dict)


class CRMAdapter(ABC):
    """What the engine is allowed to ask of a CRM."""

    @abstractmethod
    def upsert_contact(self, contact: Contact, *, external_key: str) -> Contact:
        """Create or update; idempotent on ``external_key``. Returns with ``crm_id`` set."""

    @abstractmethod
    def set_stage(self, person_id: str, *, pipeline: str, stage: str) -> None:
        """Move a contact. Callers validate legality first via ``pipelines``."""

    @abstractmethod
    def log_activity(self, activity: Activity, *, external_key: str) -> None:
        """Append to the contact's timeline."""

    @abstractmethod
    def create_task(self, task: Task) -> None:
        """Create a task, idempotent on ``task.external_key``."""

    @abstractmethod
    def sync_appointment(self, appointment: Appointment) -> None:
        """Create or update an appointment."""

    @abstractmethod
    def consume_webhook(self, raw: dict) -> WebhookEvent | None:
        """Normalize an inbound payload; ``None`` if it is a duplicate or unknown."""

    @abstractmethod
    def check_suppression(self, person_id: str) -> bool:
        """Whether the CRM believes this person is unsubscribed.

        Advisory only. The ledger's suppression list is authoritative --
        this exists to catch unsubscribes that happened in the CRM's own UI
        and need importing back.
        """
