"""The send gate. These encode the CASL rules the system must survive."""

from rayos.consent import (
    Channel,
    ConsentLedger,
    ConsentRecord,
    ConsentState,
    Purpose,
    SIX_MONTHS_SECONDS,
    SuppressionEntry,
    attest_existing_book,
)

NOW = 1_700_000_000.0
EMAIL = frozenset({Channel.EMAIL})


def ledger_with(state, *, recorded_at=NOW, expires_at=None, person="p1"):
    ledger = ConsentLedger()
    ledger.record(
        ConsentRecord(
            person_id=person,
            state=state,
            source="web_form",
            scope=EMAIL,
            recorded_at=recorded_at,
            proof="form-123",
            expires_at=expires_at,
        )
    )
    return ledger


def test_no_record_blocks_marketing():
    verdict = ConsentLedger().may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW
    )
    assert not verdict
    assert "no consent record" in verdict.reason


def test_reply_to_inbound_is_always_allowed_without_a_record():
    # Someone emailed us. Refusing to answer is not the safe behaviour.
    assert ConsentLedger().may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.REPLY, now=NOW
    )


def test_suppression_beats_everything_including_a_reply():
    ledger = ledger_with(ConsentState.EXPRESS)
    ledger.suppress(SuppressionEntry("p1", "unsubscribed", NOW))
    for purpose in Purpose:
        verdict = ledger.may_send(
            person_id="p1", channel=Channel.EMAIL, purpose=purpose, now=NOW
        )
        assert not verdict, purpose
        assert "suppressed" in verdict.reason


def test_suppression_can_be_scoped_to_one_channel():
    ledger = ledger_with(ConsentState.EXPRESS)
    ledger.record(
        ConsentRecord("p1", ConsentState.EXPRESS, "web_form",
                      frozenset({Channel.SMS}), NOW, "form-123")
    )
    ledger.suppress(SuppressionEntry("p1", "unsubscribed", NOW, channel=Channel.EMAIL))
    assert not ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW
    )
    assert ledger.may_send(
        person_id="p1", channel=Channel.SMS, purpose=Purpose.NURTURE, now=NOW
    )


def test_expired_implied_consent_blocks_marketing():
    ledger = ledger_with(
        ConsentState.IMPLIED, expires_at=NOW + SIX_MONTHS_SECONDS
    )
    later = NOW + SIX_MONTHS_SECONDS + 1
    verdict = ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=later
    )
    assert not verdict
    assert "expired" in verdict.reason


def test_expired_implied_consent_still_allows_transactional():
    # A showing reminder for an appointment they booked is not marketing.
    ledger = ledger_with(
        ConsentState.IMPLIED, expires_at=NOW + SIX_MONTHS_SECONDS
    )
    later = NOW + SIX_MONTHS_SECONDS + 1
    assert ledger.may_send(
        person_id="p1", channel=Channel.EMAIL,
        purpose=Purpose.TRANSACTIONAL, now=later,
    )


def test_withdrawn_blocks_even_transactional_marketing_paths():
    ledger = ledger_with(ConsentState.WITHDRAWN)
    assert not ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW
    )


def test_cold_send_needs_express_consent():
    implied = ledger_with(ConsentState.IMPLIED, expires_at=NOW + SIX_MONTHS_SECONDS)
    assert not implied.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.COLD, now=NOW
    )
    express = ledger_with(ConsentState.EXPRESS)
    assert express.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.COLD, now=NOW
    )


def test_latest_record_wins():
    ledger = ledger_with(ConsentState.EXPRESS, recorded_at=NOW)
    ledger.record(
        ConsentRecord("p1", ConsentState.WITHDRAWN, "reply_stop",
                      EMAIL, NOW + 10, "msg-9")
    )
    assert not ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW + 20
    )


def test_channel_scope_is_respected():
    ledger = ledger_with(ConsentState.EXPRESS)  # email only
    assert not ledger.may_send(
        person_id="p1", channel=Channel.SMS, purpose=Purpose.NURTURE, now=NOW
    )


def test_attestation_is_recorded_as_its_own_weaker_state():
    records = attest_existing_book(
        ["p1", "p2"], now=NOW, note="Ray attestation 2026-08-02", channels=EMAIL
    )
    assert len(records) == 2
    # Distinguishable from real capture evidence in any later audit.
    assert all(r.state is ConsentState.ATTESTED for r in records)
    assert all(r.source == "owner_attestation" for r in records)

    ledger = ConsentLedger()
    for record in records:
        ledger.record(record)
    assert ledger.may_send(
        person_id="p1", channel=Channel.EMAIL, purpose=Purpose.NURTURE, now=NOW
    )
