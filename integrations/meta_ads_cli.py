"""CLI to drive Meta campaigns from per-campaign config.

Every build is PAUSED. `activate` is the only thing that starts spend and
is gated on Ray's approval (the daily loop never activates on its own).

  python -m integrations.meta_ads_cli verify
  python -m integrations.meta_ads_cli build   campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli activate campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli pause    campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli insights campaigns/34-buttonleaf/meta.json
  python -m integrations.meta_ads_cli run-ops  campaigns/OPS-2026-11-03.json

run-ops applies a reviewed list of operations (pause a campaign, change a
budget, swap ad copy, finish a half-built campaign). Each op is recorded in
<ops>.state.json and skipped on a rerun, so it is safe to run twice. It
only activates a listing through an explicit activate_finished op that
names who approved it; everything else is created PAUSED.

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


def _op_pause_campaign(client: MetaAdsClient, op: dict) -> dict:
    client.for_account(op["account"]).set_status(op["campaign_id"], "PAUSED")
    return {"paused": op["campaign_id"]}


def _op_set_budget(client: MetaAdsClient, op: dict) -> dict:
    cents = int(round(float(op["daily_cad"]) * 100))
    client.for_account(op["account"]).set_daily_budget(op["adset_id"], cents)
    return {"adset_id": op["adset_id"], "daily_cad": op["daily_cad"]}


def _op_swap_copy(client: MetaAdsClient, op: dict) -> dict:
    acct = client.for_account(op["account"])
    creative_id = acct.create_video_lead_creative(
        name=op["name"], video_id=op["video_id"], thumbnail_url="",
        image_hash=op["thumbnail_hash"], message=op["message"],
        headline=op["headline"], description=op["description"],
        form_id=op["form_id"])
    acct.swap_creative(op["ad_id"], creative_id)
    return {"ad_id": op["ad_id"], "new_creative_id": creative_id}


def _op_finish(client: MetaAdsClient, op: dict, workdir: Path) -> dict:
    cfg_path = Path(op["config"])
    cfg = json.loads(cfg_path.read_text())
    ids = cfg["meta_ids"]
    acct = client.for_account(ids["ad_account_id"])
    out: dict = {}
    adset_id = ids.get("adset_id")
    if not adset_id:
        adset_id = acct.create_adset_city(
            campaign_id=ids["campaign_id"], name=op["adset_name"],
            daily_budget_cents=int(round(cfg["daily_budget_cad"] * 100)),
            city_key=op["city_key"], radius_km=int(cfg["geo"]["radius_km"]))
        ids["adset_id"] = adset_id
    out["adset_id"] = adset_id
    cr = cfg["creative"]
    ad_ids = list(ids.get("ad_ids") or [])
    for i, v in enumerate(op.get("videos", [])):
        local = acct.download(v["url"], str(workdir / f"{cfg_path.parent.name}-v{i}.mp4"))
        vid = acct.upload_video(local, title=v["name"])
        thumb = acct.wait_video_thumbnail(vid)
        cid = acct.create_video_lead_creative(
            name=v["name"], video_id=vid, thumbnail_url=thumb, message=cr["message"],
            headline=cr["headline"], description=cr["description"],
            form_id=ids["lead_form_id"])
        ad_ids.append(acct.create_ad(adset_id, v["name"], cid))
    if op.get("images"):
        hashes = []
        for i, img in enumerate(op["images"]):
            local = acct.download(img, str(workdir / f"{cfg_path.parent.name}-i{i}.jpg"))
            hashes.append(acct.upload_image(local))
        cid = acct.create_carousel_lead_creative(
            name=op["carousel_name"], message=cr["message"], headline=cr["headline"],
            description=cr["description"], image_hashes=hashes,
            form_id=ids["lead_form_id"])
        ad_ids.append(acct.create_ad(adset_id, op["carousel_name"], cid))
    ids["ad_ids"] = ad_ids
    cfg["meta_ids"] = ids
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    out["ad_ids"] = ad_ids
    return out


def _op_activate_finished(client: MetaAdsClient, op: dict) -> dict:
    """Turn ON a finished campaign. Only for listings Ray approved by name."""
    cfg = json.loads(Path(op["config"]).read_text())
    ids = cfg["meta_ids"]
    if not ids.get("adset_id") or not ids.get("ad_ids"):
        raise MetaAdsError("not finished yet (no ad set or no ads); run finish first")
    acct = client.for_account(ids["ad_account_id"])
    for ad_id in ids["ad_ids"]:
        acct.set_status(ad_id, "ACTIVE")
    acct.set_status(ids["adset_id"], "ACTIVE")
    acct.set_status(ids["campaign_id"], "ACTIVE")
    return {"live": ids["campaign_id"], "ads": ids["ad_ids"],
            "approved_by": op["approved_by"]}


def cmd_run_ops(ops_path: Path) -> None:
    import tempfile
    spec = json.loads(ops_path.read_text())
    state_path = ops_path.with_suffix(".state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    client = _client()
    workdir = Path(tempfile.mkdtemp(prefix="admax-"))
    failed = 0
    for op in spec["ops"]:
        key = op["id"]
        if state.get(key, {}).get("ok"):
            print(f"skip  {key} (already done)")
            continue
        try:
            if op["op"] == "pause_campaign":
                res = _op_pause_campaign(client, op)
            elif op["op"] == "set_budget":
                res = _op_set_budget(client, op)
            elif op["op"] == "swap_copy":
                res = _op_swap_copy(client, op)
            elif op["op"] == "finish":
                res = _op_finish(client, op, workdir)
            elif op["op"] == "activate_finished":
                if not op.get("approved_by"):
                    raise MetaAdsError("activation needs approved_by")
                res = _op_activate_finished(client, op)
            else:
                raise MetaAdsError(f"unknown op {op['op']}")
            state[key] = {"ok": True, **res}
            print(f"done  {key}: {json.dumps(res)}")
        except (MetaAdsError, OSError, KeyError, ValueError) as e:
            failed += 1
            state[key] = {"ok": False, "error": str(e)}
            print(f"FAIL  {key}: {e}", file=sys.stderr)
        state_path.write_text(json.dumps(state, indent=2))
    live = [o["id"] for o in spec["ops"] if o["op"] == "activate_finished"
            and state.get(o["id"], {}).get("ok")]
    print(f"\n{len(spec['ops']) - failed} ok, {failed} failed. "
          + (f"Switched ON: {', '.join(live)}." if live else "Nothing was activated."))
    if failed:
        raise SystemExit(1)


COMMANDS = {
    "verify": cmd_verify, "build": cmd_build, "activate": cmd_activate,
    "pause": cmd_pause, "insights": cmd_insights, "run-ops": cmd_run_ops,
}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Drive Meta campaigns for Ray Homes.")
    p.add_argument("command", choices=COMMANDS)
    p.add_argument("config", nargs="?", help="path to a campaign meta.json or ops file")
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
