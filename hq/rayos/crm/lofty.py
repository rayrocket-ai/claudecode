"""The Lofty adapter.

**Read this before running it against the live CRM.** The endpoint paths and
payload field names in :class:`Endpoints` below are drafted from the
2026-08-02 audit of Lofty's App Center and public docs; developer.lofty.com
is Cloudflare-blocked from cloud containers, so they were never executed
against the real API. They are gathered into one small class precisely so
that Phase 0's snapshot on the box corrects them in one place, and every
rule built on top stays untouched. Anything below that is *behaviour* --
idempotency, retry, throttling, ledger fallback -- is real and tested.

Three integration facts drive the design:

**Webhooks first, polling as fallback.** Integrators report sync lag up to
half an hour under load, so a poll-only design would make the system feel
broken at exactly the busy moments it needs to feel fastest.

**Redelivery is normal.** Webhook deliveries repeat. Every write therefore
carries an ``external_key`` and passes through :class:`IdempotencyStore`,
so a storm of duplicate deliveries produces one lead, not nine.

**Rate limits are real.** The transport is throttled to a minimum interval
between calls and honours ``Retry-After`` on a 429 rather than guessing, so
that a burst of activity degrades into slowness instead of into errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from .base import (
    Activity,
    Appointment,
    Contact,
    CRMAdapter,
    CRMError,
    Task,
    WebhookEvent,
)

BASE_URL = "https://api.lofty.com/v1.0"


@dataclass(frozen=True)
class Endpoints:
    """Paths and payload keys -- **verify against developer.lofty.com on the box**.

    Every value here is a guess until Phase 0 confirms it. Wrong values fail
    loudly (404 / 422), not silently, which is the one mercy of getting them
    wrong.
    """

    me: str = "/me"
    leads: str = "/leads"
    lead_by_id: str = "/leads/{id}"
    lead_search: str = "/leads/search"
    notes: str = "/leads/{id}/notes"
    tasks: str = "/tasks"
    appointments: str = "/appointments"
    pipelines: str = "/pipelines"
    webhooks: str = "/webhooks"


@dataclass(frozen=True)
class Response:
    status: int
    json: Any = None
    headers: dict[str, str] = field(default_factory=dict)


class Transport(Protocol):
    """The single seam between this adapter and the network.

    Implemented on the box by a thin `requests`/`httpx` wrapper, and by a
    recording fake in the tests. Keeping it this narrow is what lets the
    retry and idempotency logic be tested exhaustively offline.
    """

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict | None = None,
        json: dict | None = None,
    ) -> Response:
        ...


@dataclass
class IdempotencyStore:
    """Maps our ``external_key`` to the CRM id it produced.

    In memory here; a table with a unique index on the box, because the
    guarantee has to survive a worker restart mid-storm to be worth having.
    """

    seen: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self.seen.get(key)

    def put(self, key: str, crm_id: str) -> None:
        self.seen[key] = crm_id

    def __contains__(self, key: str) -> bool:
        return key in self.seen


@dataclass
class RetryPolicy:
    """Backoff for the failures worth retrying, and only those.

    4xx other than 429 are not retried: a malformed payload sent five times
    is still malformed, and the retries only obscure the error in the logs.
    """

    max_attempts: int = 4
    base_delay: float = 2.0
    max_delay: float = 30.0
    retry_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504})

    def delay_for(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None:
            # The server told us. Guessing over top of that is how you get
            # rate-limited for longer.
            return min(retry_after, self.max_delay)
        return min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)


@dataclass
class LoftyAdapter(CRMAdapter):
    """Lofty implementation of :class:`~rayos.crm.base.CRMAdapter`."""

    transport: Transport
    api_key: str
    #: Seconds to wait between calls. Lofty's published limits are vague, so
    #: this starts conservative and gets tuned from observed 429s on the box.
    min_interval: float = 0.25
    base_url: str = BASE_URL
    endpoints: Endpoints = field(default_factory=Endpoints)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    idempotency: IdempotencyStore = field(default_factory=IdempotencyStore)
    seen_deliveries: set[str] = field(default_factory=set)
    #: Injected so tests do not sleep and the box can use real time. These
    #: use default_factory rather than a plain default on purpose: a bare
    #: function as a class-level default is a descriptor, so `self.sleep(x)`
    #: would bind and pass `self` as the first argument. Assigning per
    #: instance sidesteps that entirely.
    sleep: Callable[[float], None] = field(
        default_factory=lambda: (lambda _seconds: None)
    )
    clock: Callable[[], float] = field(default_factory=lambda: (lambda: 0.0))
    #: None means "never called". A float sentinel of 0.0 would silently
    #: disable throttling under any monotonic clock that starts at zero.
    _last_call_at: float | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    # -- plumbing --------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        # Lofty uses a token scheme rather than Bearer -- confirmed from the
        # App Center docs panel in the 2026-08-02 screenshot audit.
        return {
            "Authorization": f"token {self.api_key}",
            "Content-Type": "application/json",
        }

    def _throttle(self) -> None:
        now = self.clock()
        if self._last_call_at is not None:
            elapsed = now - self._last_call_at
            if elapsed < self.min_interval:
                self.sleep(self.min_interval - elapsed)
        self._last_call_at = self.clock()

    def _call(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> Response:
        url = f"{self.base_url}{path}"
        self.calls.append((method, path))
        last: Response | None = None

        for attempt in range(1, self.retry.max_attempts + 1):
            self._throttle()
            response = self.transport.request(
                method, url, headers=self._headers(), params=params, json=json
            )
            last = response

            if 200 <= response.status < 300:
                return response
            if response.status not in self.retry.retry_statuses:
                raise CRMError(
                    f"{method} {path} failed with {response.status}: {response.json!r}"
                )
            if attempt == self.retry.max_attempts:
                break

            retry_after = response.headers.get("Retry-After")
            self.sleep(
                self.retry.delay_for(
                    attempt, float(retry_after) if retry_after else None
                )
            )

        raise CRMError(
            f"{method} {path} still failing after {self.retry.max_attempts} "
            f"attempts (last status {last.status if last else 'none'})"
        )

    # -- the interface ---------------------------------------------------
    def upsert_contact(self, contact: Contact, *, external_key: str) -> Contact:
        known = self.idempotency.get(external_key)
        if known is not None:
            # A redelivered webhook or a retried job. Update, never create.
            contact.crm_id = known
            self._call(
                "PUT",
                self.endpoints.lead_by_id.format(id=known),
                json=self._contact_payload(contact),
            )
            return contact

        if contact.crm_id:
            response = self._call(
                "PUT",
                self.endpoints.lead_by_id.format(id=contact.crm_id),
                json=self._contact_payload(contact),
            )
        else:
            response = self._call(
                "POST", self.endpoints.leads, json=self._contact_payload(contact)
            )

        crm_id = self._extract_id(response) or contact.crm_id
        if crm_id is None:
            raise CRMError("Lofty returned no id for an upserted lead")
        contact.crm_id = crm_id
        self.idempotency.put(external_key, crm_id)
        return contact

    def set_stage(self, person_id: str, *, pipeline: str, stage: str) -> None:
        crm_id = self._require_crm_id(person_id)
        self._call(
            "PUT",
            self.endpoints.lead_by_id.format(id=crm_id),
            json={"pipeline": pipeline, "stage": stage},
        )

    def log_activity(self, activity: Activity, *, external_key: str) -> None:
        if external_key in self.idempotency:
            return
        crm_id = self._require_crm_id(activity.person_id)
        self._call(
            "POST",
            self.endpoints.notes.format(id=crm_id),
            json={
                "type": activity.kind,
                "content": activity.summary,
                "occurred_at": activity.occurred_at,
            },
        )
        self.idempotency.put(external_key, crm_id)

    def create_task(self, task: Task) -> None:
        if task.external_key in self.idempotency:
            return
        crm_id = self._require_crm_id(task.person_id)
        response = self._call(
            "POST",
            self.endpoints.tasks,
            json={
                "lead_id": crm_id,
                "title": task.title,
                "due_at": task.due_at,
                "assignee": task.owner,
                "priority": "high" if task.hard_deadline else "normal",
            },
        )
        self.idempotency.put(task.external_key, self._extract_id(response) or crm_id)

    def sync_appointment(self, appointment: Appointment) -> None:
        crm_id = self._require_crm_id(appointment.person_id)
        existing = self.idempotency.get(appointment.external_key)
        payload = {
            "lead_id": crm_id,
            "type": appointment.kind,
            "start": appointment.starts_at,
            "end": appointment.ends_at,
            "location": appointment.location,
        }
        if existing is not None:
            self._call("PUT", f"{self.endpoints.appointments}/{existing}", json=payload)
            return
        response = self._call("POST", self.endpoints.appointments, json=payload)
        appointment_id = self._extract_id(response)
        if appointment_id:
            self.idempotency.put(appointment.external_key, appointment_id)

    def consume_webhook(self, raw: dict) -> WebhookEvent | None:
        """Normalize, and drop redeliveries.

        Returning ``None`` rather than raising is deliberate: a duplicate is
        not an error condition, it is the expected steady state of a webhook
        integration, and the caller should acknowledge it with a 200 so the
        vendor stops retrying.
        """
        delivery_id = str(
            raw.get("delivery_id") or raw.get("eventId") or raw.get("id") or ""
        )
        if not delivery_id or delivery_id in self.seen_deliveries:
            return None
        self.seen_deliveries.add(delivery_id)

        kind = str(raw.get("event") or raw.get("type") or "unknown")
        return WebhookEvent(
            kind=kind,
            crm_id=str(raw.get("leadId") or raw.get("lead_id") or raw.get("id") or ""),
            occurred_at=float(raw.get("timestamp") or raw.get("ts") or 0.0),
            delivery_id=delivery_id,
            payload=raw,
        )

    def check_suppression(self, person_id: str) -> bool:
        crm_id = self._require_crm_id(person_id)
        response = self._call("GET", self.endpoints.lead_by_id.format(id=crm_id))
        body = response.json or {}
        return bool(
            body.get("unsubscribed")
            or body.get("doNotContact")
            or body.get("do_not_contact")
        )

    # -- helpers ---------------------------------------------------------
    _crm_ids: dict[str, str] = field(default_factory=dict)

    def remember(self, person_id: str, crm_id: str) -> None:
        """Seed the identity map (from the ledger, on startup)."""
        self._crm_ids[person_id] = crm_id

    def _require_crm_id(self, person_id: str) -> str:
        crm_id = self._crm_ids.get(person_id)
        if crm_id is None:
            raise CRMError(
                f"no Lofty id known for {person_id!r} -- upsert the contact first"
            )
        return crm_id

    def _contact_payload(self, contact: Contact) -> dict:
        """Map our model onto Lofty's, with the ledger fallback.

        Fields Lofty has no home for are not dropped and not crammed into a
        notes blob -- they stay in the ledger and the contact carries a
        ``ledger:<field>`` tag so a human looking at the CRM can see that
        more is known and where to find it.
        """
        payload: dict[str, Any] = {
            "firstName": contact.first_name,
            "lastName": contact.last_name,
            "emails": list(contact.emails),
            "phones": list(contact.phones),
            "source": contact.source,
            "assignee": contact.owner,
            "tags": sorted(contact.merged_tags()),
        }
        if contact.pipeline:
            payload["pipeline"] = contact.pipeline
        if contact.stage:
            payload["stage"] = contact.stage
        if contact.language and contact.language != "en":
            payload["language"] = contact.language
        return payload

    @staticmethod
    def _extract_id(response: Response) -> str | None:
        body = response.json
        if not isinstance(body, dict):
            return None
        for key in ("id", "leadId", "lead_id"):
            if body.get(key):
                return str(body[key])
        data = body.get("data")
        if isinstance(data, dict):
            for key in ("id", "leadId", "lead_id"):
                if data.get(key):
                    return str(data[key])
        return None
