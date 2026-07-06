"""Unit tests for the Listing Launch Agent (drafting + delivery orchestration)."""

import asyncio
import json
from types import SimpleNamespace

import integrations.campaign as campaign_mod
from ai.listing_agent import CAMPAIGN_TOOL, format_listing_facts
from bot.handlers.listing import _build_listing, _format_campaign_preview
from integrations.campaign import (
    ChannelResult,
    build_open_house_ics,
    launch_campaign,
    run_email_blast,
    run_feature_sheet,
)


def _run(coro):
    return asyncio.run(coro)


# ── Agent input shaping ────────────────────────────────────────────


class TestFormatListingFacts:
    def test_includes_only_nonempty_fields(self):
        facts = format_listing_facts({
            "address": "12 Main St, Toronto",
            "price": 899000,
            "bedrooms": "",        # empty → omitted
            "features": [],        # empty → omitted
        })
        assert "Address: 12 Main St, Toronto" in facts
        assert "List price: 899000" in facts
        assert "Bedrooms" not in facts   # compliance: never surface blanks

    def test_lists_are_joined(self):
        facts = format_listing_facts({"features": ["pool", "finished basement"]})
        assert "pool, finished basement" in facts

    def test_no_details_is_explicit(self):
        assert "no structured details" in format_listing_facts({})


class TestCampaignTool:
    def test_schema_is_serializable(self):
        json.dumps(CAMPAIGN_TOOL)
        assert CAMPAIGN_TOOL["name"] == "submit_campaign"
        props = CAMPAIGN_TOOL["input_schema"]["properties"]
        for field in ("listing_copy_long", "feature_sheet", "reel_script", "email", "sms"):
            assert field in props


# ── Listing intake (handler) ───────────────────────────────────────


class TestBuildListing:
    def test_free_text_becomes_description_and_address(self):
        listing = _run(_build_listing("45 King St W\n3 bed, 2 bath, huge backyard"))
        assert listing["description"].startswith("45 King St W")
        assert listing["address"] == "45 King St W"

    def test_plain_text_without_address(self):
        listing = _run(_build_listing("charming bungalow, must see"))
        assert "description" in listing
        assert "address" not in listing


# ── Delivery channels (graceful degradation) ───────────────────────


SAMPLE = {
    "listing_copy_long": "A lovely home.",
    "feature_sheet": {"headline": "Bright & Spacious", "highlights": ["A", "B", "C"]},
    "reel_script": {"hook": "Wow", "shots": ["s1", "s2"], "cta": "DM me"},
    "email": {"subject": "Just Listed", "body_html": "<p>See it</p>"},
    "sms": "Just listed at 12 Main St — book a showing!",
    "open_house": {"title": "Open House", "description": "Come by",
                   "day_of_week": "Saturday", "time_range": "2-4pm"},
}


class TestChannels:
    def test_feature_sheet_drafted(self):
        r = _run(run_feature_sheet(SAMPLE))
        assert r.status == "drafted" and r.ok
        assert r.payload["headline"] == "Bright & Spacious"

    def test_missing_asset_is_skipped(self):
        r = _run(run_feature_sheet({}))
        assert r.status == "skipped" and not r.ok

    def test_email_without_recipients_is_drafted(self):
        r = _run(run_email_blast(SAMPLE, recipients=None))
        assert r.status == "drafted"
        assert "no recipients" in r.detail

    def test_email_sent_when_smtp_and_recipients(self, monkeypatch):
        sent = {}

        async def fake_send_email(to, subject, body, attachment_path=None):
            sent["to"] = to
            return True

        monkeypatch.setattr(campaign_mod, "send_email", fake_send_email)
        monkeypatch.setattr(
            campaign_mod, "get_settings",
            lambda: SimpleNamespace(is_smtp_configured=True, gamma_api_key="",
                                    higgsfield_api_key="", boosend_api_key="",
                                    marketing_open_house_duration=120),
        )
        r = _run(run_email_blast(SAMPLE, recipients=["buyer@example.com"]))
        assert r.status == "sent"
        assert sent["to"] == ["buyer@example.com"]


class TestOpenHouseIcs:
    def test_builds_valid_ics(self):
        ics = build_open_house_ics(SAMPLE)
        assert ics is not None
        assert "BEGIN:VCALENDAR" in ics and "END:VCALENDAR" in ics
        assert "SUMMARY:Open House" in ics

    def test_none_when_no_open_house(self):
        assert build_open_house_ics({}) is None


class TestLaunchCampaign:
    def test_runs_all_channels_and_never_raises(self):
        results = _run(launch_campaign(SAMPLE, recipients=None))
        channels = {r.channel for r in results}
        assert channels == {"feature_sheet", "reel", "email", "sms", "open_house"}
        # Nothing configured for direct send → all drafted, none failed.
        assert all(r.status in ("drafted", "sent") for r in results)

    def test_partial_campaign_skips_missing(self):
        results = _run(launch_campaign({"sms": "hi"}, recipients=None))
        by_channel = {r.channel: r.status for r in results}
        assert by_channel["sms"] == "drafted"
        assert by_channel["feature_sheet"] == "skipped"

    def test_channel_selection(self):
        results = _run(launch_campaign(SAMPLE, channels=["sms"]))
        assert len(results) == 1 and results[0].channel == "sms"


class TestChannelResult:
    def test_ok_property(self):
        assert ChannelResult("x", "sent").ok
        assert ChannelResult("x", "drafted").ok
        assert not ChannelResult("x", "skipped").ok
        assert not ChannelResult("x", "failed").ok


class TestCampaignPreview:
    def test_summarizes_assets(self):
        text = _format_campaign_preview(SAMPLE)
        assert "Campaign drafted" in text
        assert "Feature sheet" in text
        assert "Open house" in text
