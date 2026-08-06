"""Lofty adapter behaviour, proven without a key or a network.

The endpoint paths are unverified (see the module docstring in lofty.py) --
what these tests lock down is everything that would still be wrong if the
paths were perfect: duplicate webhooks creating duplicate people, retries
hammering a rate-limited API, 4xx errors being retried into oblivion.
"""

import pytest

from rayos.crm.base import Activity, Appointment, Contact, CRMError, PartyType, Task
from rayos.crm.lofty import LoftyAdapter, Response


class FakeTransport:
    """Records calls and replays scripted responses."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])
        self.default = Response(200, {"id": "lofty-1"})

    def request(self, method, url, *, headers, params=None, json=None):
        self.calls.append(
            {"method": method, "url": url, "headers": headers,
             "params": params, "json": json}
        )
        if self.responses:
            return self.responses.pop(0)
        return self.default


def adapter(responses=None, **kwargs):
    slept = []
    transport = FakeTransport(responses)
    # Off by default so retry-backoff assertions are not polluted by
    # throttle waits; the throttle has its own test below.
    kwargs.setdefault("min_interval", 0.0)
    crm = LoftyAdapter(
        transport=transport,
        api_key="test-key",
        sleep=slept.append,
        **kwargs,
    )
    return crm, transport, slept


def contact(person_id="p1"):
    return Contact(
        person_id=person_id,
        first_name="Sam",
        last_name="Okafor",
        emails=["sam@example.com"],
        party_types={PartyType.BUYER},
        source="vow",
        owner="ray",
    )


# -- auth -----------------------------------------------------------------

def test_uses_lofty_token_scheme_not_bearer():
    crm, transport, _ = adapter()
    crm.upsert_contact(contact(), external_key="k1")
    assert transport.calls[0]["headers"]["Authorization"] == "token test-key"


# -- idempotency ----------------------------------------------------------

def test_duplicate_external_key_updates_instead_of_creating():
    crm, transport, _ = adapter()
    crm.upsert_contact(contact(), external_key="webhook-77")
    crm.upsert_contact(contact(), external_key="webhook-77")

    methods = [c["method"] for c in transport.calls]
    assert methods == ["POST", "PUT"]  # created once, then updated


def test_duplicate_webhook_storm_creates_one_lead():
    crm, transport, _ = adapter()
    for _ in range(9):
        crm.upsert_contact(contact(), external_key="webhook-77")
    posts = [c for c in transport.calls if c["method"] == "POST"]
    assert len(posts) == 1


def test_redelivered_webhook_is_dropped():
    crm, _, _ = adapter()
    raw = {"delivery_id": "d1", "event": "contact.created", "id": "lofty-9"}
    assert crm.consume_webhook(raw) is not None
    assert crm.consume_webhook(raw) is None


def test_webhook_without_a_delivery_id_is_dropped():
    crm, _, _ = adapter()
    assert crm.consume_webhook({"event": "contact.created"}) is None


def test_webhook_normalizes_vendor_field_variants():
    crm, _, _ = adapter()
    event = crm.consume_webhook(
        {"eventId": "d2", "type": "stage.changed", "leadId": "L9", "timestamp": 5.0}
    )
    assert event.kind == "stage.changed"
    assert event.crm_id == "L9"
    assert event.occurred_at == 5.0


def test_repeated_activity_logs_once():
    crm, transport, _ = adapter()
    crm.remember("p1", "lofty-1")
    activity = Activity("p1", "email_sent", "Sent the intro", 1.0)
    crm.log_activity(activity, external_key="msg-1")
    crm.log_activity(activity, external_key="msg-1")
    assert len([c for c in transport.calls if c["method"] == "POST"]) == 1


def test_repeated_task_creates_once():
    crm, transport, _ = adapter()
    crm.remember("p1", "lofty-1")
    task = Task("p1", "Call back", 10.0, "ray", external_key="t-1")
    crm.create_task(task)
    crm.create_task(task)
    assert len(transport.calls) == 1


def test_appointment_reschedule_updates_the_same_record():
    crm, transport, _ = adapter()
    crm.remember("p1", "lofty-1")
    first = Appointment("p1", "showing", 100.0, 200.0, external_key="appt-1")
    crm.sync_appointment(first)
    moved = Appointment("p1", "showing", 300.0, 400.0, external_key="appt-1")
    crm.sync_appointment(moved)
    assert [c["method"] for c in transport.calls] == ["POST", "PUT"]


# -- retry and rate limits ------------------------------------------------

def test_429_is_retried_and_honours_retry_after():
    crm, transport, slept = adapter(
        responses=[
            Response(429, None, {"Retry-After": "7"}),
            Response(200, {"id": "lofty-1"}),
        ]
    )
    crm.upsert_contact(contact(), external_key="k1")
    # The server said seven seconds. Guessing shorter is how you stay limited.
    assert slept[0] == 7.0


def test_backoff_is_exponential_without_a_retry_after_header():
    crm, _, slept = adapter(
        responses=[
            Response(500), Response(502), Response(200, {"id": "lofty-1"})
        ]
    )
    crm.upsert_contact(contact(), external_key="k1")
    assert slept == [2.0, 4.0]


def test_gives_up_after_max_attempts():
    crm, transport, _ = adapter(responses=[Response(503)] * 6)
    with pytest.raises(CRMError, match="still failing"):
        crm.upsert_contact(contact(), external_key="k1")
    assert len([c for c in transport.calls if c["method"] == "POST"]) == 4


def test_client_errors_are_not_retried():
    # A malformed payload sent five times is still malformed; retrying only
    # buries the real error in the log.
    crm, transport, _ = adapter(responses=[Response(422, {"error": "bad field"})])
    with pytest.raises(CRMError, match="422"):
        crm.upsert_contact(contact(), external_key="k1")
    assert len(transport.calls) == 1


def test_throttle_waits_between_calls():
    clock = {"t": 0.0}
    crm, _, slept = adapter(min_interval=0.5, clock=lambda: clock["t"])
    crm.upsert_contact(contact(), external_key="k1")
    crm.upsert_contact(contact("p2"), external_key="k2")
    assert slept and slept[0] == pytest.approx(0.5)


# -- payload mapping ------------------------------------------------------

def test_party_types_become_tags():
    crm, transport, _ = adapter()
    person = contact()
    person.party_types = {PartyType.BUYER, PartyType.INVESTOR}
    crm.upsert_contact(person, external_key="k1")
    tags = transport.calls[0]["json"]["tags"]
    assert "pt:buyer" in tags and "pt:investor" in tags


def test_ledger_fields_are_flagged_not_dropped():
    # Lofty cannot hold it, so the ledger does -- and the CRM shows a pointer
    # rather than pretending the data does not exist.
    crm, transport, _ = adapter()
    person = contact()
    person.ledger_fields = {"consent_proof": "form-993"}
    crm.upsert_contact(person, external_key="k1")
    assert "ledger:consent_proof" in transport.calls[0]["json"]["tags"]


def test_id_is_extracted_from_a_nested_data_envelope():
    crm, _, _ = adapter(responses=[Response(201, {"data": {"leadId": "L42"}})])
    result = crm.upsert_contact(contact(), external_key="k1")
    assert result.crm_id == "L42"


def test_missing_id_in_response_is_an_error():
    crm, _, _ = adapter(responses=[Response(201, {"ok": True})])
    with pytest.raises(CRMError, match="no id"):
        crm.upsert_contact(contact(), external_key="k1")


def test_operations_need_a_known_crm_id_first():
    crm, _, _ = adapter()
    with pytest.raises(CRMError, match="upsert the contact first"):
        crm.set_stage("ghost", pipeline="buyer", stage="qualified")


def test_suppression_read_recognises_vendor_field_variants():
    crm, _, _ = adapter(responses=[Response(200, {"do_not_contact": True})])
    crm.remember("p1", "lofty-1")
    assert crm.check_suppression("p1") is True
