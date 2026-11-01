"""Post formats: showcase / explainer / full laid over an edit."""

import json
from pathlib import Path

import pytest

from reelforge.core import brand as brand_mod
from reelforge.core import post
from reelforge.core.edl import EDL, CaptionWord, Captions, Overlay, Segment


def make_edl(**kw) -> EDL:
    base = dict(source="/src.mp4", segments=[Segment("s1", 0.0, 6.0), Segment("s2", 10.0, 16.0)],
                captions=Captions(style="karaoke-bold", position=0.7, words=[
                    CaptionWord("Write", 0.2, 0.5), CaptionWord("this.", 0.5, 0.9),
                    CaptionWord("Comment", 10.0, 10.4), CaptionWord("edit.", 10.4, 10.9)]))
    base.update(kw)
    return EDL(**base)


def test_showcase_splits_and_puts_captions_on_the_seam():
    spec = {"format": "showcase", "ratio": 0.45,
            "top": [{"at": 0, "dur": 4, "kind": "prompt", "text": "/edit", "result": "/r.png"}]}
    out, notes = post.apply(make_edl(), spec)
    assert out.layout.kind == "split" and out.layout.ratio == 0.45
    assert out.captions.style == "seam" and out.captions.position is None
    assert out.layout.top[0].text == "/edit"
    assert out.target.loudness == post.SOCIAL_LOUDNESS
    assert notes == []


def test_clips_are_clamped_and_never_overlap():
    spec = {"format": "explainer", "top": [
        {"at": 0, "dur": 5, "kind": "image", "asset": "/d.png"},
        {"at": 4, "dur": 3, "kind": "image", "asset": "/d.png"},
        {"at": 11.9, "dur": 5, "kind": "image", "asset": "/d.png"}]}
    out, notes = post.apply(make_edl(), spec)
    top = out.layout.top
    assert top[1].at == 5.0                      # pushed past the first
    assert len(top) == 2                         # the last had no room
    assert any("moved" in n for n in notes) and any("dropped" in n for n in notes)
    assert top[0].pan_from == post.DEFAULT_PAN[0]   # explainers drift by default


def test_end_card_takes_brand_and_the_last_seconds():
    b = brand_mod.Brand(handle="@ray", accent="#123456")
    out, _ = post.apply(make_edl(), {"format": "full", "end_card": {"keyword": '"edit"', "dur": 3}}, b)
    card = out.end_card
    assert card.keyword == "EDIT" and card.handle == "@ray" and card.accent == "#123456"
    assert card.at == pytest.approx(9.0) and card.dur == 3.0
    assert out.layout.kind == "full"


def test_end_card_cannot_swallow_a_short_edit():
    e = EDL(source="/s.mp4", segments=[Segment("s1", 0, 5)])
    out, notes = post.apply(e, {"format": "full", "end_card": {"keyword": "X", "dur": 4}})
    assert out.end_card.dur == pytest.approx(2.0)
    assert any("shortened" in n for n in notes)


def test_split_drops_full_frame_overlays():
    e = make_edl(overlays=[Overlay(type="remotion", at=1.0, dur=2.0, comp="lower-third")])
    out, notes = post.apply(e, {"format": "showcase", "top": []})
    assert out.overlays == [] and any("overlay" in n for n in notes)
    assert len(e.overlays) == 1                 # the original edit is untouched


def test_bad_specs_say_what_is_wrong():
    with pytest.raises(post.PostError, match="unknown format"):
        post.apply(make_edl(), {"format": "carousel"})
    with pytest.raises(post.PostError, match="prompt with no text"):
        post.apply(make_edl(), {"format": "showcase", "top": [{"at": 0, "dur": 2, "kind": "prompt"}]})
    with pytest.raises(post.PostError, match="no asset"):
        post.apply(make_edl(), {"format": "explainer", "top": [{"at": 0, "dur": 2, "kind": "image"}]})
    with pytest.raises(post.PostError, match="keyword"):
        post.apply(make_edl(), {"format": "full", "end_card": {"keyword": " "}})


def test_relative_assets_resolve_against_the_spec(tmp_path):
    spec = {"format": "explainer", "top": [{"at": 0, "dur": 2, "kind": "image", "asset": "d.png"}]}
    out, _ = post.apply(make_edl(), spec, base=tmp_path)
    assert out.layout.top[0].asset == str((tmp_path / "d.png").resolve())


def test_laid_out_edl_round_trips(tmp_path):
    spec = {"format": "showcase", "top": [{"at": 0, "dur": 3, "kind": "prompt", "text": "x"}],
            "end_card": {"keyword": "EDIT"}}
    out, _ = post.apply(make_edl(), spec)
    path = tmp_path / "p.edl.json"
    out.save(path)
    again = EDL.load(path)
    assert again.layout.top[0].text == "x" and again.end_card.keyword == "EDIT"


def test_request_shows_the_edit_on_its_own_clock():
    text = post.post_request(make_edl(), ["/a.png"], keyword="edit", offer="the prompts")
    assert "[  0.2s] Write this." in text and "[ 10.0s] Comment edit." in text
    assert "EDIT" in text and "the prompts" in text and "- /a.png" in text


def test_schema_formats_match_the_code():
    assert post.POST_SCHEMA["properties"]["format"]["enum"] == list(post.FORMATS)


def test_brand_loads_defaults_and_ignores_junk(tmp_path):
    assert brand_mod.load(tmp_path).accent == "#FF6B2C"
    (tmp_path / "brand.json").write_text(json.dumps({"handle": "@me", "nonsense": 1}))
    b = brand_mod.load(tmp_path)
    assert b.handle == "@me" and b.primary == "#0A2540"
    (tmp_path / "brand.json").write_text("{not json")
    assert brand_mod.load(tmp_path).handle == ""
