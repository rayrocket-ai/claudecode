"""CLI to drive Meta campaigns from per-campaign config.

Every build is PAUSED. `activate` is the only thing that starts spend and
is gated on Ray's approval (the daily loop never activates on its own).

  python -m integrations.meta_ads_cli verify
  python -m integrations.meta_ads_cli build   campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli activate campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli pause    campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli insights campaigns/34-buttonleaf/meta.json

Build writes the created object IDs next to the config as
<slug>/meta_state.json so later commands know what to act on.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import Settings
from integrations.meta_ads import MetaAdsClient, MetaAdsError, MetaCreds


def _client() -> MetaAdsClient:
    creds = MetaCreds.from_settings(Settings())
    missing = creds.missing()
    if missing:
        print("Missing credentials in .env: " + ", ".join(missing), file=sys.stderr)
        print("See META_ADS_SETUP.md for how to get each one.", file=sys.stderr)
        raise SystemExit(2)
    return MetaAdsClient(creds)


def _state_path(config_path: Path) -> Path:
    return config_path.parent / "meta_state.json"


def _load_state(config_path: Path) -> dict:
    p = _state_path(config_path)
    return json.loads(p.read_text()) if p.exists() else {}


def _save_state(config_path: Path, state: dict) -> None:
    _state_path(config_path).write_text(json.dumps(state, indent=2))


def cmd_verify(_config: Path | None) -> None:
    acct = _client().verify()
    print(json.dumps(acct, indent=2))


def cmd_build(config_path: Path) -> None:
    cfg = json.loads(config_path.read_text())
    client = _client()
    state = _load_state(config_path)

    if state.get("campaign_id"):
        print(f"Already built (campaign {state['campaign_id']}). "
              f"Delete {_state_path(config_path)} to rebuild.", file=sys.stderr)
        raise SystemExit(1)

    form_id = client.create_lead_form(
        name=cfg["name"] + " form",
        questions=cfg["form"]["questions"],
        privacy_url=cfg["form"]["privacy_url"],
        intro_headline=cfg["form"]["intro_headline"],
        thank_you=cfg["form"]["thank_you"],
    )
    campaign_id = client.create_campaign(cfg["name"])
    adset_id = client.create_adset(
        campaign_id=campaign_id,
        name=cfg["name"] + " adset",
        daily_budget_cents=int(round(cfg["daily_budget_cad"] * 100)),
        lat=cfg["geo"]["lat"], lng=cfg["geo"]["lng"],
        radius_km=cfg["geo"]["radius_km"], form_id=form_id,
    )
    image_hashes = [client.upload_image(p) for p in cfg["creative"]["image_paths"]]
    creative_id = client.create_carousel_creative(
        name=cfg["name"] + " creative",
        message=cfg["creative"]["message"],
        headline=cfg["creative"]["headline"],
        description=cfg["creative"]["description"],
        image_hashes=image_hashes,
        link=cfg["creative"]["link"],
    )
    ad_id = client.create_ad(adset_id, cfg["name"] + " ad", creative_id)

    state = {"campaign_id": campaign_id, "adset_id": adset_id,
             "form_id": form_id, "creative_id": creative_id, "ad_id": ad_id,
             "status": "PAUSED"}
    _save_state(config_path, state)
    print("Built (all PAUSED). Nothing is spending yet.")
    print(json.dumps(state, indent=2))
    print("\nApprove, then run: activate " + str(config_path))


def cmd_activate(config_path: Path) -> None:
    state = _load_state(config_path)
    if not state.get("campaign_id"):
        print("Nothing built yet. Run build first.", file=sys.stderr)
        raise SystemExit(1)
    client = _client()
    client.set_status(state["adset_id"], "ACTIVE")
    client.set_status(state["ad_id"], "ACTIVE")
    client.set_status(state["campaign_id"], "ACTIVE")
    state["status"] = "ACTIVE"
    _save_state(config_path, state)
    print(f"LIVE. Campaign {state['campaign_id']} is now spending.")


def cmd_pause(config_path: Path) -> None:
    state = _load_state(config_path)
    if not state.get("campaign_id"):
        print("Nothing built yet.", file=sys.stderr)
        raise SystemExit(1)
    _client().set_status(state["campaign_id"], "PAUSED")
    state["status"] = "PAUSED"
    _save_state(config_path, state)
    print(f"Paused campaign {state['campaign_id']}.")


def cmd_insights(config_path: Path) -> None:
    state = _load_state(config_path)
    if not state.get("campaign_id"):
        print("Nothing built yet.", file=sys.stderr)
        raise SystemExit(1)
    data = _client().insights(state["campaign_id"], date_preset="yesterday")
    if data["leads"]:
        data["cpl"] = round(data["spend"] / data["leads"], 2)
    print(json.dumps(data, indent=2))


COMMANDS = {
    "verify": cmd_verify, "build": cmd_build, "activate": cmd_activate,
    "pause": cmd_pause, "insights": cmd_insights,
}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Drive Meta campaigns for Ray Homes.")
    p.add_argument("command", choices=COMMANDS)
    p.add_argument("config", nargs="?", help="path to a campaign meta.json")
    args = p.parse_args(argv)

    config_path = Path(args.config) if args.config else None
    if args.command != "verify" and config_path is None:
        p.error(f"{args.command} needs a config path")
    try:
        COMMANDS[args.command](config_path)
    except MetaAdsError as e:
        print(f"Meta API error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
