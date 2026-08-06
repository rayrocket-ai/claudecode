"""An in-memory CRM adapter.

Two jobs: it is what the rest of the system is tested against, and it is
what runs in development before a Lofty key exists. It implements the same
idempotency contract as the real adapter, so a test that passes here is
testing the contract rather than the fake.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import Activity, Appointment, Contact, CRMAdapter, Task, WebhookEvent


@dataclass
class InMemoryCRM(CRMAdapter):
    contacts: dict[str, Contact] = field(default_factory=dict)
    activities: list[Activity] = field(default_factory=list)
    tasks: dict[str, Task] = field(default_factory=dict)
    appointments: dict[str, Appointment] = field(default_factory=dict)
    suppressed: set[str] = field(default_factory=set)
    seen_keys: set[str] = field(default_factory=set)
    seen_deliveries: set[str] = field(default_factory=set)
    _next_id: int = 1

    def upsert_contact(self, contact: Contact, *, external_key: str) -> Contact:
        existing = self.contacts.get(contact.person_id)
        if existing is not None:
            contact.crm_id = existing.crm_id
        else:
            contact.crm_id = f"mem-{self._next_id}"
            self._next_id += 1
        contact.tags = contact.merged_tags()
        self.contacts[contact.person_id] = contact
        self.seen_keys.add(external_key)
        return contact

    def set_stage(self, person_id: str, *, pipeline: str, stage: str) -> None:
        contact = self.contacts[person_id]
        contact.pipeline = pipeline
        contact.stage = stage

    def log_activity(self, activity: Activity, *, external_key: str) -> None:
        if external_key in self.seen_keys:
            return
        self.seen_keys.add(external_key)
        self.activities.append(activity)

    def create_task(self, task: Task) -> None:
        self.tasks.setdefault(task.external_key, task)

    def sync_appointment(self, appointment: Appointment) -> None:
        self.appointments[appointment.external_key] = appointment

    def consume_webhook(self, raw: dict) -> WebhookEvent | None:
        delivery_id = str(raw.get("delivery_id", ""))
        if not delivery_id or delivery_id in self.seen_deliveries:
            return None
        self.seen_deliveries.add(delivery_id)
        return WebhookEvent(
            kind=str(raw.get("event", "unknown")),
            crm_id=str(raw.get("id", "")),
            occurred_at=float(raw.get("ts", 0.0)),
            delivery_id=delivery_id,
            payload=raw,
        )

    def check_suppression(self, person_id: str) -> bool:
        return person_id in self.suppressed
