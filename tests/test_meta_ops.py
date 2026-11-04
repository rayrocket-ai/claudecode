"""run-ops: pause, budget, copy swap and finish, fully mocked."""

import json

from integrations import meta_ads_cli
from integrations.meta_ads import MetaAdsClient, MetaCreds


class Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code, self.text = payload, status, json.dumps(payload)

    def json(self):
        return self._p


class Fake:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def post(self, url, data=None, files=None, **kw):
        self.calls.append(("POST", url, data))
        return self.responses.pop(0)

    def get(self, url, params=None, **kw):
        self.calls.append(("GET", url, params))
        return self.responses.pop(0)


def _client(fake):
    return MetaAdsClient(MetaCreds("tok", "act_1", "PAGE", "IG"), fake)


def test_for_account_adds_act_prefix():
    c = _client(Fake([])).for_account("1788")
    assert c.creds.ad_account_id == "act_1788"
    assert c.creds.page_id == "PAGE"


def test_city_adset_refuses_small_radius():
    import pytest
    with pytest.raises(ValueError):
        _client(Fake([])).create_adset_city("C", "n", 500, "292371", 20)


def test_run_ops_pause_budget_and_finish_without_media(tmp_path, monkeypatch):
    cfg = tmp_path / "meta.json"
    cfg.write_text(json.dumps({"daily_budget_cad": 5.0, "geo": {"radius_km": 25},
                               "creative": {"message": "m", "headline": "h", "description": "d"},
                               "meta_ids": {"ad_account_id": "1788", "campaign_id": "CAMP",
                                            "lead_form_id": "FORM", "adset_id": None,
                                            "ad_ids": []}}))
    ops = tmp_path / "ops.json"
    ops.write_text(json.dumps({"ops": [
        {"id": "p", "op": "pause_campaign", "account": "7326", "campaign_id": "CURRY"},
        {"id": "b", "op": "set_budget", "account": "7326", "adset_id": "AS", "daily_cad": 5},
        {"id": "f", "op": "finish", "config": str(cfg), "city_key": "292371",
         "adset_name": "x"},
    ]}))
    fake = Fake([Resp({"success": True}), Resp({"success": True}), Resp({"id": "NEWADSET"})])
    monkeypatch.setattr(meta_ads_cli, "_client", lambda: _client(fake))
    meta_ads_cli.cmd_run_ops(ops)

    assert fake.calls[0][1].endswith("/CURRY") and fake.calls[0][2]["status"] == "PAUSED"
    assert fake.calls[1][1].endswith("/AS") and fake.calls[1][2]["daily_budget"] == 500
    adset = fake.calls[2][2]
    assert fake.calls[2][1].endswith("act_1788/adsets")
    assert adset["status"] == "PAUSED" and adset["daily_budget"] == 500
    assert json.loads(adset["targeting"])["geo_locations"]["cities"][0]["radius"] == 25
    assert json.loads(cfg.read_text())["meta_ids"]["adset_id"] == "NEWADSET"

    # Rerun is a no-op: every op is recorded as done.
    fake2 = Fake([])
    monkeypatch.setattr(meta_ads_cli, "_client", lambda: _client(fake2))
    meta_ads_cli.cmd_run_ops(ops)
    assert fake2.calls == []


def test_swap_copy_builds_lead_video_creative_then_repoints_ad(tmp_path, monkeypatch):
    ops = tmp_path / "ops.json"
    ops.write_text(json.dumps({"ops": [{"id": "s", "op": "swap_copy", "account": "7326",
        "ad_id": "AD", "name": "n", "video_id": "V", "thumbnail_hash": "H",
        "form_id": "F", "message": "no address here", "headline": "h", "description": "d"}]}))
    fake = Fake([Resp({"id": "CR"}), Resp({"success": True})])
    monkeypatch.setattr(meta_ads_cli, "_client", lambda: _client(fake))
    meta_ads_cli.cmd_run_ops(ops)
    spec = json.loads(fake.calls[0][2]["object_story_spec"])
    assert spec["video_data"]["image_hash"] == "H"
    assert spec["video_data"]["call_to_action"]["value"]["lead_gen_form_id"] == "F"
    assert json.loads(fake.calls[1][2]["creative"]) == {"creative_id": "CR"}


def test_real_ops_file_only_activates_what_ray_approved():
    spec = json.loads(open("campaigns/OPS-2026-11-03.json").read())
    assert {o["op"] for o in spec["ops"]} <= {"pause_campaign", "set_budget", "swap_copy",
                                              "finish", "activate_finished",
                                              "add_video_ad", "report"}
    for o in spec["ops"]:
        if o.get("activate"):
            assert o.get("approved_by") and o["account"] == "732663023528570"
    acts = [o for o in spec["ops"] if o["op"] == "activate_finished"]
    assert [o["config"] for o in acts] == ["campaigns/53-alpha/meta.json"]
    assert all(o.get("approved_by") for o in acts)
    order = [o["id"] for o in spec["ops"]]
    assert order.index("finish-53-alpha") < order.index("activate-53-alpha")


def test_activate_refuses_unfinished_campaign(tmp_path, monkeypatch):
    cfg = tmp_path / "meta.json"
    cfg.write_text(json.dumps({"meta_ids": {"ad_account_id": "1", "campaign_id": "C",
                                            "adset_id": None, "ad_ids": []}}))
    ops = tmp_path / "ops.json"
    ops.write_text(json.dumps({"ops": [{"id": "a", "op": "activate_finished",
                                        "config": str(cfg), "approved_by": "Ray"}]}))
    fake = Fake([])
    monkeypatch.setattr(meta_ads_cli, "_client", lambda: _client(fake))
    import pytest
    with pytest.raises(SystemExit):
        meta_ads_cli.cmd_run_ops(ops)
    assert fake.calls == []


def test_report_prints_and_always_reruns(tmp_path, monkeypatch, capsys):
    ops = tmp_path / "ops.json"
    ops.write_text(json.dumps({"ops": [{"id": "r", "op": "report", "campaigns": {
        "x": {"account": "1", "campaign_id": "C"}}}]}))
    row = {"data": [{"spend": "10.0", "impressions": "1000", "ctr": "2.0",
                     "actions": [{"action_type": "lead", "value": "2"}]}]}
    for _ in range(2):
        fake = Fake([Resp(row), Resp(row), Resp(row)])
        monkeypatch.setattr(meta_ads_cli, "_client", lambda: _client(fake))
        meta_ads_cli.cmd_run_ops(ops)
        assert len(fake.calls) == 3
    out = capsys.readouterr().out
    assert '"cpl": 5.0' in out
