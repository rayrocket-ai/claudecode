"""End-to-end: a lead arrives and moves, with every gate in the path.

These are the tests that would have caught the failures the plan was written
to fix -- a lead with no next action, an unapproved send going out, a
duplicate webhook splitting a person in two.
"""

from rayos.checklists import EIGHT_BY_EIGHT, fan_out
from rayos.consent import (
    Channel,
    ConsentLedger,
    ConsentRecord,
    ConsentState,
    Purpose,
)
from rayos.crm import Contact, InMemoryCRM
from rayos.crm.base import PartyType, Task as CRMTask
from rayos.pipelines import BUYER, LeadPosition, idle_breaches
from rayos.policy import TokenLedger, mint_from_telegram_callback
from rayos.workorders import State, WorkOrder, WorkOrderQueue

RAY = 7
ALLOWED = frozenset({RAY})
NOW = 1_700_000_000.0


def test_new_lead_lands_staged_owned_and_with_a_next_action():
    """Phase 1's exit criterion, as a test."""
    crm = InMemoryCRM()
    person = Contact(
        person_id="p1",
        first_name="Ada",
        emails=["ada@example.com"],
        party_types={PartyType.BUYER},
        source="calculator",
        owner="concierge",
        pipeline="buyer",
        stage="new_lead",
    )
    crm.upsert_contact(person, external_key="intake-1")

    tasks = fan_out(EIGHT_BY_EIGHT, person_id="p1", anchor=NOW)
    for task in tasks[:1]:
        crm.create_task(
            CRMTask("p1", task.title, task.due_at, task.owner, task.key)
        )

    stored = crm.contacts["p1"]
    assert stored.crm_id
    assert stored.owner and stored.stage and stored.source
    assert crm.tasks, "a lead with no next action is exactly the failure mode"


def test_intake_from_a_duplicate_webhook_does_not_split_the_person():
    crm = InMemoryCRM()
    for _ in range(5):
        crm.upsert_contact(Contact(person_id="p1"), external_key="wh-1")
    assert len(crm.contacts) == 1


def test_lead_walks_the_buyer_pipeline_legally():
    crm = InMemoryCRM()
    crm.upsert_contact(
        Contact(person_id="p1", pipeline="buyer", stage="new_lead"),
        external_key="intake-1",
    )
    path = [
        "contact_attempted", "in_qualification", "qualified",
        "consult_booked", "consult_done_bra", "vow_active_searching",
    ]
    current = "new_lead"
    for nxt in path:
        BUYER.assert_transition(current, nxt)  # raises if the move is illegal
        crm.set_stage("p1", pipeline="buyer", stage=nxt)
        current = nxt
    assert crm.contacts["p1"].stage == "vow_active_searching"


def test_a_silent_new_lead_surfaces_within_two_minutes():
    positions = [LeadPosition("p1", "buyer", "new_lead", NOW)]
    assert idle_breaches(positions, now=NOW + 119) == []
    assert idle_breaches(positions, now=NOW + 121)


def test_nurture_send_requires_consent_and_the_send_gate_is_not_a_prompt():
    ledger = ConsentLedger()
    verdict = ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW
    )
    assert not verdict

    ledger.record(
        ConsentRecord("p1", ConsentState.EXPRESS, "vow_registration",
                      frozenset({Channel.EMAIL}), NOW, "reg-1")
    )
    assert ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW
    )


def test_offer_cannot_be_sent_without_rays_thumb():
    queue = WorkOrderQueue()
    wo = queue.submit(
        WorkOrder(role="buyer_specialist", action_class="send_offer",
                  subject_id="p1", created_at=NOW)
    )
    wo.start(now=NOW)
    assert wo.state is State.BLOCKED
    assert queue.blocked() == [wo]

    token = mint_from_telegram_callback(
        action_class="send_offer", subject_id="p1", approver_id=RAY,
        authorized_ids=ALLOWED, now=NOW, nonce="tap-1",
    )
    tokens = TokenLedger()
    wo.start(now=NOW + 1, token=token, ledger=tokens)
    wo.finish("offer delivered", now=NOW + 2)

    assert wo.state is State.DONE
    assert queue.blocked() == []


def test_one_approval_does_not_authorize_a_second_send():
    tokens = TokenLedger()
    token = mint_from_telegram_callback(
        action_class="send_offer", subject_id="p1", approver_id=RAY,
        authorized_ids=ALLOWED, now=NOW, nonce="tap-1",
    )
    first = WorkOrder(role="bs", action_class="send_offer",
                      subject_id="p1", created_at=NOW)
    second = WorkOrder(role="bs", action_class="send_offer",
                       subject_id="p1", created_at=NOW)

    assert first.start(now=NOW, token=token, ledger=tokens).allowed
    assert not second.start(now=NOW, token=token, ledger=tokens).allowed
    assert second.state is State.BLOCKED
