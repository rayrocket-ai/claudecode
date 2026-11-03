"""The virtual camera: shot planning from one angle, and generated angles."""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from reelforge.core import camera
from reelforge.core.analyze import Signals
from reelforge.core.edl import EDL, CaptionWord, Captions, Framing, Segment, Shot, validate


@dataclass
class Info:
    width: int
    height: int
    duration: float = 60.0


UHD = Info(3840, 2160)


def talking(n_words=60, gap_every=6) -> list[CaptionWord]:
    words, t = [], 0.0
    for i in range(n_words):
        text = f"w{i}" + ("." if i % gap_every == gap_every - 1 else "")
        words.append(CaptionWord(text, round(t, 3), round(t + 0.3, 3)))
        t += 0.35 + (0.25 if i % gap_every == gap_every - 1 else 0.0)
    return words


def edit(**kw) -> EDL:
    base = dict(source="/s.mp4", segments=[Segment("s1", 0.0, 12.0), Segment("s2", 20.0, 32.0)],
                captions=Captions(words=talking(58)))
    base.update(kw)
    return EDL(**base)


def all_shots(e: EDL):
    return [(f.seg, s) for f in e.framing for s in f.shots]


def test_every_segment_gets_shots_and_the_edit_still_validates():
    plan = camera.plan(edit(), UHD, Signals(duration=40, focus=[(0, 0.4, 0.3)]))
    assert {f.seg for f in plan.edl.framing if f.shots} == {"s1", "s2"}
    assert plan.shots == len(all_shots(plan.edl)) and plan.shots >= 6
    assert validate(plan.edl) == []
    assert plan.notes == []                       # 4K has room for every size


def test_shots_cut_on_word_starts_every_couple_of_seconds():
    e = edit()
    plan = camera.plan(e, UHD, None)
    starts = {w.start for w in e.captions.words}
    for f in plan.edl.framing:
        seg_start = 0.0 if f.seg == "s1" else 12.0
        ats = [s.at for s in f.shots]
        assert ats[0] == 0.0
        for a in ats[1:]:
            assert round(seg_start + a, 3) in starts
        gaps = [b - a for a, b in zip(ats, ats[1:])]
        assert all(1.4 <= g <= 4.0 for g in gaps)


def test_consecutive_shots_never_share_a_size_or_a_move():
    plan = camera.plan(edit(), UHD, None)
    shots = [s for _, s in all_shots(plan.edl)]
    for a, b in zip(shots, shots[1:]):
        assert a.size != b.size
        assert a.move != b.move or a.move == "punch"


def test_the_hook_opens_close_and_emphasis_punches():
    e = edit(framing=[Framing(seg="s2", mode="punch", zoom_to=1.14)])
    plan = camera.plan(e, UHD, None)
    first = plan.edl.framing_for("s1").shots[0]
    assert first.size == "close"
    s2 = plan.edl.framing_for("s2").shots[0]
    assert s2.move == "punch" and s2.size in ("extreme", "close")


def test_small_sources_get_a_squeezed_ladder_and_a_warning():
    plan = camera.plan(edit(), Info(1920, 1080), None)
    zooms = {s.zoom for _, s in all_shots(plan.edl)}
    assert max(zooms) <= plan.max_zoom + 1e-6 < 2.4
    assert any("4K" in n for n in plan.notes)
    ladder = camera.sizes_for(1.46)
    assert ladder["wide"] < ladder["medium"] < ladder["close"] < ladder["extreme"] <= 1.46


def test_styles_differ_and_unknown_style_is_refused():
    doc = camera.plan(edit(), UHD, None, style="documentary")
    multi = camera.plan(edit(), UHD, None, style="multicam")
    assert doc.shots < multi.shots                 # longer takes
    assert all(s.drift > 0 for _, s in all_shots(doc.edl))
    with pytest.raises(ValueError):
        camera.plan(edit(), UHD, None, style="drone")


def test_peek_goes_on_the_side_away_from_the_subject():
    plan = camera.plan(edit(), UHD, Signals(duration=40, focus=[(0, 0.3, 0.3)]), style="cinematic")
    peeks = [s.peek for _, s in all_shots(plan.edl) if s.peek]
    assert peeks and set(peeks) == {"right"}


def test_no_words_still_cuts_on_time():
    e = edit(captions=Captions(words=[]))
    plan = camera.plan(e, UHD, None)
    assert all(len(f.shots) >= 3 for f in plan.edl.framing)


def test_plan_does_not_touch_the_original():
    e = edit()
    camera.plan(e, UHD, None)
    assert e.framing == []


def test_shots_round_trip_through_json(tmp_path):
    plan = camera.plan(edit(), UHD, None)
    path = tmp_path / "c.edl.json"
    plan.edl.save(path)
    again = EDL.load(path)
    assert [(s.at, s.size, s.focus) for _, s in all_shots(again)] == \
           [(s.at, s.size, s.focus) for _, s in all_shots(plan.edl)]


def test_validate_catches_broken_shot_lists():
    e = edit(framing=[Framing(seg="s1", shots=[Shot(at=0.5), Shot(at=0.4, zoom=9.0)])])
    problems = " ".join(validate(e))
    assert "first shot must start at 0" in problems
    assert "does not start after" in problems
    assert "zoom 9.0" in problems


# --------------------------------------------------------------------------
# generated angles
# --------------------------------------------------------------------------

def test_angle_picks_are_long_spread_and_skip_the_hook():
    plan = camera.plan(edit(), UHD, None)
    picks = camera.pick_for_angles(plan.edl, 2)
    assert len(picks) == 2
    assert all(p["dur"] >= 1.5 for p in picks)
    assert not any(p["seg"] == "s1" and p["shot"] == 0 for p in picks)
    assert picks[0]["src_in"] < picks[1]["src_in"]


def test_ingest_locks_the_clip_to_the_voice(tmp_path):
    plan = camera.plan(edit(), UHD, None)
    pick = camera.pick_for_angles(plan.edl, 1)[0]
    manifest = tmp_path / camera.MANIFEST
    manifest.write_text(json.dumps({"angles": [{**pick, "name": "angle-01",
                                                "request_dur": pick["dur"] + 0.05}]}))
    results = tmp_path / "results"
    results.mkdir()
    (results / "angle-01.mp4").write_bytes(b"x")
    probe = lambda p: Info(1, 1, duration=(pick["dur"] + 0.05) * 1.1)
    out, notes = camera.ingest_angles(plan.edl, manifest, results, probe=probe)
    shot = out.framing_for(pick["seg"]).shots[pick["shot"]]
    assert shot.size == "angle" and shot.angle.endswith("angle-01.mp4")
    assert shot.angle_rate == pytest.approx(1.1, abs=1e-3)
    assert "placed" in notes[0]
    assert plan.edl.framing_for(pick["seg"]).shots[pick["shot"]].angle == ""


def test_ingest_refuses_clips_too_far_off_and_stale_plans(tmp_path):
    plan = camera.plan(edit(), UHD, None)
    pick = camera.pick_for_angles(plan.edl, 1)[0]
    manifest = tmp_path / camera.MANIFEST
    manifest.write_text(json.dumps({"angles": [
        {**pick, "name": "angle-01"},
        {**pick, "name": "angle-02", "src_in": 999.0, "src_out": 1001.0}]}))
    results = tmp_path / "r"
    results.mkdir()
    for n in ("angle-01", "angle-02"):
        (results / f"{n}.mov").write_bytes(b"x")
    out, notes = camera.ingest_angles(plan.edl, manifest, results,
                                      probe=lambda p: Info(1, 1, duration=pick["dur"] * 1.6))
    assert "too far off" in notes[0] and "plan changed" in notes[1]
    assert all(s.size != "angle" for _, s in all_shots(out))


def test_missing_results_are_reported_not_fatal(tmp_path):
    plan = camera.plan(edit(), UHD, None)
    pick = camera.pick_for_angles(plan.edl, 1)[0]
    manifest = tmp_path / camera.MANIFEST
    manifest.write_text(json.dumps({"angles": [{**pick, "name": "angle-01"}]}))
    _, notes = camera.ingest_angles(plan.edl, manifest, tmp_path / "none")
    assert "no generated clip yet" in notes[0]


def test_detail_shots_are_rare_even_when_hands_never_stop(monkeypatch):
    # a presenter gesturing the whole time: every probe finds strong motion
    monkeypatch.setattr(camera, "motion_focus", lambda src, t, face: (0.5, 0.75, 0.5))
    e = edit()
    plan = camera.plan(e, UHD, None, src=Path("/s.mp4"))
    times, elapsed = [], 0.0
    for seg in plan.edl.segments:
        for sh in plan.edl.framing_for(seg.id).shots:
            if sh.size == "detail":
                times.append(elapsed + sh.at)
        elapsed += seg.out_duration
    assert times, "motion should still earn an insert"
    assert all(b - a >= camera.STYLES["multicam"].detail_gap for a, b in zip(times, times[1:]))
    assert len(times) <= 1 + plan.edl.duration // camera.STYLES["multicam"].detail_gap
