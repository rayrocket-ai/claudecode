"""The safety spine. If any of these fail, nothing else in the system is safe."""

import pytest

from rayos.policy import (
    ApprovalToken,
    ForgedTokenError,
    Tier,
    TOKEN_TTL_SECONDS,
    TokenLedger,
    authorize,
    mint_from_telegram_callback,
    tier_for,
)

RAY = 12345
ALLOWED = frozenset({RAY})


def mint(action="send_offer", subject="lead-1", now=1000.0, nonce="n1", approver=RAY):
    return mint_from_telegram_callback(
        action_class=action,
        subject_id=subject,
        approver_id=approver,
        authorized_ids=ALLOWED,
        now=now,
        nonce=nonce,
    )


# -- fail closed ----------------------------------------------------------

def test_unknown_action_requires_approval():
    assert tier_for("wire_the_deposit_somewhere") is Tier.APPROVE


def test_unknown_action_cannot_run_without_a_token():
    decision = authorize(
        action_class="wire_the_deposit_somewhere", subject_id="x", now=1000.0
    )
    assert not decision
    assert "no token" in decision.reason


def test_known_dangerous_actions_are_approve_tier():
    for action in (
        "send_offer",
        "send_legal_document",
        "spend_money",
        "delete_records",
        "publish_content",
        "send_cold_message",
        "change_listing_price",
    ):
        assert tier_for(action) is Tier.APPROVE, action


def test_drafting_is_always_free():
    for action in ("draft_message", "draft_offer", "draft_content"):
        assert tier_for(action) is Tier.AUTO


# -- the Phase-0 gate -----------------------------------------------------

def test_inbound_reply_is_gated_until_phase_zero_passes():
    assert tier_for("reply_inbound_lead", inbound_auto=False) is Tier.APPROVE
    assert tier_for("reply_inbound_lead", inbound_auto=True) is Tier.AUTO


# -- tokens cannot be forged ---------------------------------------------

def test_token_cannot_be_constructed_directly():
    with pytest.raises(ForgedTokenError):
        ApprovalToken(object(), "send_offer", "lead-1", RAY, 1000.0, "n1")


def test_unauthorized_user_cannot_mint():
    with pytest.raises(PermissionError):
        mint(approver=999)


def test_empty_allowlist_denies_everyone():
    # A config that failed to load must not turn into "everyone is an admin".
    with pytest.raises(PermissionError):
        mint_from_telegram_callback(
            action_class="send_offer",
            subject_id="lead-1",
            approver_id=RAY,
            authorized_ids=frozenset(),
            now=1000.0,
            nonce="n1",
        )


# -- tokens are narrow, expiring, and single-use -------------------------

def test_token_authorizes_its_own_action():
    token = mint()
    assert authorize(
        action_class="send_offer", subject_id="lead-1", now=1000.0, token=token
    )


def test_token_does_not_authorize_a_different_action():
    token = mint(action="send_offer")
    decision = authorize(
        action_class="spend_money", subject_id="lead-1", now=1000.0, token=token
    )
    assert not decision
    assert "different action" in decision.reason


def test_token_does_not_authorize_a_different_subject():
    token = mint(subject="lead-1")
    decision = authorize(
        action_class="send_offer", subject_id="lead-2", now=1000.0, token=token
    )
    assert not decision
    assert "different subject" in decision.reason


def test_token_expires():
    token = mint(now=1000.0)
    late = 1000.0 + TOKEN_TTL_SECONDS + 1
    decision = authorize(
        action_class="send_offer", subject_id="lead-1", now=late, token=token
    )
    assert not decision
    assert "expired" in decision.reason


def test_token_is_single_use():
    ledger = TokenLedger()
    token = mint()
    first = authorize(
        action_class="send_offer", subject_id="lead-1", now=1000.0,
        token=token, ledger=ledger,
    )
    second = authorize(
        action_class="send_offer", subject_id="lead-1", now=1001.0,
        token=token, ledger=ledger,
    )
    assert first
    assert not second
    assert "already used" in second.reason


def test_auto_and_notify_need_no_token():
    assert authorize(action_class="draft_message", subject_id="x", now=0.0)
    assert authorize(action_class="send_nurture_message", subject_id="x", now=0.0)
