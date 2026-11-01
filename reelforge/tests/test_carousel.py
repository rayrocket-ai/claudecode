"""Carousels: parsing the brain's copy, requests, props, and the CLI path."""

import json
from pathlib import Path

import pytest

from reelforge.core import carousel as car
from reelforge.core.brand import Brand


def payload(n_slides=6, **extra):
    slides = [{"role": "body", "headline": f"Point *{i}*", "body": "b"} for i in range(n_slides)]
    return {"carousels": [{"angle": "An angle", "caption": "Line one", "slides": slides,
                           "hashtags": ["reels", "#ai", "two words"], **extra}]}


def test_first_slide_is_the_hook_and_last_the_cta_whatever_was_written():
    plans, notes = car.parse(payload())
    roles = [s.role for s in plans[0].slides]
    assert roles[0] == "hook" and roles[-1] == "cta" and set(roles[1:-1]) == {"body"}
    assert plans[0].hashtags == ["#reels", "#ai", "#twowords"]
    assert notes == []


def test_too_many_slides_keeps_the_cta():
    p = payload(14)
    p["carousels"][0]["slides"][-1]["headline"] = "The ask"
    plans, notes = car.parse(p)
    assert len(plans[0].slides) == car.MAX_SLIDES
    assert plans[0].slides[-1].headline == "The ask"
    assert any("trimmed" in n for n in notes)


def test_unusable_carousels_are_dropped_and_none_raises():
    p = payload()
    p["carousels"].append({"angle": "thin", "slides": [{"role": "hook", "headline": "x"}], "caption": ""})
    plans, notes = car.parse(p)
    assert len(plans) == 1 and any("dropped" in n for n in notes)
    with pytest.raises(car.CarouselError):
        car.parse({"carousels": []})


def test_requests_carry_the_three_inputs_or_the_reel():
    brief = car.brief_request(problem="P", context="C", idea="I", variants=3,
                              keyword="carrusel", offer="the skill")
    assert "3 carousels" in brief and "P" in brief and "borrow its structure" in brief
    assert "CARRUSEL" in brief and "the skill" in brief
    reel = car.reel_request(transcript="[00:01.0] hi", context="", variants=1, keyword=None, offer=None)
    assert "into 1 carousel." in reel and "already performed" in reel and "## Context" not in reel


def test_props_carry_brand_and_keyword():
    plans, _ = car.parse(payload())
    props = car.props(plans[0], Brand(handle="@me"), "edit")
    assert props["keyword"] == "EDIT" and props["brand"]["handle"] == "@me"
    assert props["width"] == 1080 and props["height"] == 1350
    assert props["slides"][0]["role"] == "hook"


def test_render_cmd_is_a_png_sequence():
    cmd = car.render_cmd(Path("/p"), Path("/props.json"), Path("/out"), Path("/chrome"))
    assert "Carousel" in cmd and "--sequence" in cmd and "--image-format=png" in cmd
    assert "--browser-executable=/chrome" in cmd


def test_save_writes_caption_and_replayable_decision(tmp_path):
    plans, _ = car.parse(payload())
    car.save(plans[0], tmp_path, "EDIT")
    assert (tmp_path / "caption.txt").read_text().startswith("Line one\n\n#reels")
    again, _ = car.parse(json.loads((tmp_path / "carousel.json").read_text()))
    assert [s.headline for s in again[0].slides] == [s.headline for s in plans[0].slides]


def test_schema_slide_bounds_match_the_code():
    items = car.CAROUSEL_SCHEMA["properties"]["carousels"]["items"]["properties"]["slides"]
    assert items["minItems"] == car.MIN_SLIDES and items["maxItems"] == car.MAX_SLIDES


def test_cli_brief_without_inputs_says_what_is_missing(tmp_path, monkeypatch, capsys):
    from reelforge import cli

    monkeypatch.setenv("REELFORGE_ROOT", str(tmp_path))
    assert cli.main(["carousel", "--problem", "p"]) == 2
    err = capsys.readouterr().err
    assert "--context" in err and "--idea" in err


def test_cli_replays_a_decision_without_rendering(tmp_path, monkeypatch, capsys):
    from reelforge import cli

    monkeypatch.setenv("REELFORGE_ROOT", str(tmp_path))
    d = tmp_path / "d.json"
    d.write_text(json.dumps({**payload(), "keyword": "edit"}))
    assert cli.main(["carousel", "--decision", str(d), "--no-render",
                     "--outdir", str(tmp_path / "out")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["keyword"] == "EDIT"
    folder = Path(report["carousels"][0]["folder"])
    assert (folder / "caption.txt").exists() and folder.name.startswith("01-an-angle")


def test_cli_brain_path_uses_the_carousel_writer(tmp_path, monkeypatch, capsys):
    from reelforge import cli
    from reelforge.core import agent

    monkeypatch.setenv("REELFORGE_ROOT", str(tmp_path))
    seen = {}

    def fake(self, request, *, style_profile=None):
        seen["request"] = request
        return agent.Decision(payload=payload(), model="m")

    monkeypatch.setattr(agent.Brain, "write_carousel", fake)
    assert cli.main(["carousel", "--problem", "no time", "--context", "a realtor",
                     "--idea", "5 mistakes", "--no-render", "--outdir", str(tmp_path / "o")]) == 0
    assert "no time" in seen["request"] and "5 mistakes" in seen["request"]
