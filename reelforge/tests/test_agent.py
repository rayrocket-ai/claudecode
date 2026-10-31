"""The standalone editor agent.

No network here: the brain is driven by a fake client that records what was
sent and replays a scripted answer. What these tests pin down is the part that
would be wrong even with a perfect model -- that the request carries the real
agent prompt, forces the tool, caches the system prompt, and that the answer
flows through the same compose and render path as /reels.
"""

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from reelforge import cli
from reelforge.core import agent, media
from reelforge.core.analyze import Signals
from reelforge.core.cache import Cache, content_key
from reelforge.core.highlights import HIGHLIGHTS_SCHEMA
from reelforge.core.playbook import Playbook
from reelforge.core.transcribe import Transcript, Word
from reelforge.core.vlog import EPISODE_SCHEMA

CLIP = {"start": 1.0, "end": 9.0, "hook": "Here is the thing",
        "why": "stands alone", "emphasis": [3.0],
        "scores": {"hook": 8, "self_contained": 7, "payoff": 6, "quotable": 5}}


class FakeClient:
    def __init__(self, payload, *, tool="submit_highlights", stop="tool_use",
                 block_type="tool_use"):
        self.calls = []
        self._payload, self._tool, self._stop, self._type = payload, tool, stop, block_type
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        block = SimpleNamespace(type=self._type, name=self._tool, input=self._payload)
        return SimpleNamespace(content=[block], stop_reason=self._stop,
                               usage=SimpleNamespace(input_tokens=1200, output_tokens=340))


def transcript(n=30) -> Transcript:
    words = [Word(f"w{i}", 0.4 * i, 0.4 * i + 0.3) for i in range(n)]
    return Transcript(words=words, language="en", duration=0.4 * n, model="test")


# --------------------------------------------------------------------------
# prompt material
# --------------------------------------------------------------------------

def test_agent_prompt_is_the_real_agent_file_without_frontmatter():
    prompt = agent.agent_prompt("editor")
    assert not prompt.startswith("---")
    assert "name: editor" not in prompt
    assert "What makes a clip" in prompt              # from agents/editor.md
    assert "StructuredOutput" not in prompt           # rewritten for the API tool


def test_style_profile_is_appended_and_outranks_defaults():
    prompt = agent.agent_prompt("producer", "Never cut the sign-off.")
    assert prompt.rstrip().endswith("Never cut the sign-off.")
    assert "outranks every default" in prompt


def test_transcript_breaks_on_pauses_and_carries_tenths():
    t = Transcript(words=[Word("one", 0.0, 0.3), Word("two", 0.35, 0.6),
                          Word("three", 83.4, 83.8)],
                   language="en", duration=90.0, model="test")
    lines = agent.transcript_text(t).splitlines()
    assert lines == ["[00:00.0] one two", "[01:23.4] three"]


def test_long_runs_are_broken_into_readable_lines():
    lines = agent.transcript_text(transcript(40)).splitlines()
    assert all(len(line.split("] ")[1].split()) <= agent.LINE_WORDS for line in lines)


def test_signals_summary_is_compact_and_survives_absence():
    assert "No visual" in agent.signals_summary(None)
    s = Signals(duration=60.0, silence=[(10.0, 13.0)], scenes=[5.0, 20.0],
                energy=[0.1] * 59 + [0.9])
    text = agent.signals_summary(s)
    assert "Longest silences" in text and "Scene cuts (2)" in text
    assert "00:59.0=0.90" in text


def test_reels_request_asks_for_three_times_the_count():
    text = agent.reels_request(transcript(), None, count=3, book=Playbook())
    assert "roughly 9 candidates" in text
    assert "[00:00.0]" in text


# --------------------------------------------------------------------------
# the call
# --------------------------------------------------------------------------

def test_find_clips_forces_the_tool_and_caches_the_system_prompt():
    client = FakeClient({"clips": [CLIP]})
    decision = agent.Brain(client=client, model="m-test").find_clips(
        transcript(), None, count=2, book=Playbook())

    call = client.calls[0]
    assert call["model"] == "m-test"
    assert call["tool_choice"] == {"type": "tool", "name": "submit_highlights"}
    assert call["tools"][0]["input_schema"] is HIGHLIGHTS_SCHEMA
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "What makes a clip" in call["system"][0]["text"]

    assert len(decision.clips) == 1 and decision.clips[0].hook == "Here is the thing"
    assert decision.usage() == {"model": "m-test", "input_tokens": 1200, "output_tokens": 340}


def test_shape_episode_uses_the_producer_and_the_episode_schema():
    client = FakeClient({"body": {"start": 0, "end": 10}, "drop": [], "chapters": [],
                         "title": "T"}, tool="submit_episode")
    decision = agent.Brain(client=client).shape_episode(transcript(), None)
    call = client.calls[0]
    assert call["tools"][0]["input_schema"] is EPISODE_SCHEMA
    assert "long-form video editor" in call["system"][0]["text"]
    assert decision.payload["title"] == "T"


def test_no_usable_clips_is_an_error_with_the_raw_answer():
    client = FakeClient({"clips": [{"start": 5, "end": 2, "hook": "", "why": "",
                                    "scores": {}}]})
    with pytest.raises(agent.AgentError, match="no usable clips"):
        agent.Brain(client=client).find_clips(transcript(), None, count=1, book=Playbook())


def test_running_out_of_tokens_says_so():
    client = FakeClient({"clips": [CLIP]}, stop="max_tokens")
    with pytest.raises(agent.AgentError, match="out of output tokens"):
        agent.Brain(client=client).find_clips(transcript(), None, count=1, book=Playbook())


def test_an_answer_without_the_tool_is_an_error():
    client = FakeClient("hello", block_type="text")
    with pytest.raises(agent.AgentError, match="did not return a decision"):
        agent.Brain(client=client).find_clips(transcript(), None, count=1, book=Playbook())


def test_model_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("REELFORGE_MODEL", "claude-from-env")
    assert agent.Brain(client=object()).model == "claude-from-env"
    monkeypatch.delenv("REELFORGE_MODEL")
    assert agent.Brain(client=object()).model == agent.DEFAULT_MODEL


def test_missing_key_names_the_fix(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(agent.AgentError, match="ANTHROPIC_API_KEY"):
        agent.default_client()


# --------------------------------------------------------------------------
# the whole command
# --------------------------------------------------------------------------

def seeded_source(tmp_path: Path, monkeypatch) -> Path:
    """A real clip with its transcript already cached -- no whisper needed."""
    monkeypatch.setenv("REELFORGE_ROOT", str(tmp_path / "root"))
    src = tmp_path / "talk.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=12",
        "-f", "lavfi", "-i", "sine=frequency=300:duration=12",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", str(src)], check=True)
    cache = Cache(tmp_path / "root" / ".cache")
    key = content_key(src)
    words = [Word(f"word{i}", 0.5 + 0.5 * i, 0.9 + 0.5 * i) for i in range(22)]
    cache.write_json(key, "words.json",
                     Transcript(words=words, language="en", duration=12.0,
                                model="test").as_dict())
    cache.write_json(key, "signals.json", Signals(duration=12.0).as_dict())
    return src


@pytest.mark.skipif(not media.available(), reason="ffmpeg not installed")
def test_edit_replays_a_decision_through_compose_and_render(tmp_path, monkeypatch, capsys):
    src = seeded_source(tmp_path, monkeypatch)
    decision = tmp_path / "decision.json"
    decision.write_text(json.dumps({"clips": [CLIP]}))
    outdir = tmp_path / "out"

    code = cli.main(["edit", str(src), "--decision", str(decision), "--count", "1",
                     "--outdir", str(outdir), "--engine", "ffmpeg", "--draft",
                     "--width", "540", "--qc-passes", "1"])
    report = json.loads(capsys.readouterr().out)

    assert report["mode"] == "reels"
    assert Path(report["decision"]).exists()           # the decision is kept
    reel = report["reels"][0]
    assert Path(reel["edl"]).exists()
    assert reel["render"]["engine"] == "ffmpeg"
    out = Path(reel["render"]["output"])
    assert out.exists() and media.probe(out).width == 540
    assert Path(report["report"]).exists()
    assert code in (0, 1)                              # 1 only if QC left findings


def test_edit_calls_the_brain_when_there_is_no_decision(tmp_path, monkeypatch, capsys):
    src = seeded_source(tmp_path, monkeypatch)
    client = FakeClient({"clips": [CLIP]})
    monkeypatch.setattr(agent, "default_client", lambda: client)

    code = cli.main(["edit", str(src), "--count", "1", "--outdir", str(tmp_path / "o"),
                     "--no-render"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert len(client.calls) == 1
    assert report["usage"]["input_tokens"] == 1200
    saved = json.loads(Path(report["decision"]).read_text())
    assert saved["clips"][0]["hook"] == "Here is the thing"


def test_edit_reports_a_missing_key_cleanly(tmp_path, monkeypatch, capsys):
    src = seeded_source(tmp_path, monkeypatch)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    code = cli.main(["edit", str(src), "--no-render", "--outdir", str(tmp_path / "o")])
    assert code == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_edit_vlog_mode_replays_an_episode(tmp_path, monkeypatch, capsys):
    src = seeded_source(tmp_path, monkeypatch)
    decision = tmp_path / "episode.json"
    decision.write_text(json.dumps({"body": {"start": 0.5, "end": 11.5}, "drop": [],
                                    "chapters": [], "title": "My episode"}))
    code = cli.main(["edit", str(src), "--mode", "vlog", "--decision", str(decision),
                     "--outdir", str(tmp_path / "o"), "--no-render"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["mode"] == "vlog" and report["title"] == "My episode"
    assert Path(report["edl"]).exists()


def test_env_file_supplies_the_key_without_overriding_exports(tmp_path, monkeypatch):
    env = tmp_path / "env"
    env.write_text('# secrets\nexport ANTHROPIC_API_KEY="from-file"\nREELFORGE_MODEL=m-file\n\nnot a line\n')
    env.chmod(0o600)
    monkeypatch.setenv("REELFORGE_ENV_FILE", str(env))
    # setenv-then-delenv, not delenv alone: delenv on an absent variable
    # records nothing to undo, and the key this test loads would leak into
    # every test after it.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "placeholder")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.setenv("REELFORGE_MODEL", "m-exported")
    cli._load_env_file()
    import os
    assert os.environ["ANTHROPIC_API_KEY"] == "from-file"
    assert os.environ["REELFORGE_MODEL"] == "m-exported"      # an export still wins


def test_a_missing_env_file_is_fine(tmp_path, monkeypatch):
    monkeypatch.setenv("REELFORGE_ENV_FILE", str(tmp_path / "absent"))
    cli._load_env_file()                                       # must not raise


def test_transcript_command_prints_what_the_brain_reads(tmp_path, monkeypatch, capsys):
    src = seeded_source(tmp_path, monkeypatch)
    assert cli.main(["transcript", str(src)]) == 0
    out = capsys.readouterr().out
    assert "## Signals" in out and "## Transcript" in out
    assert "[00:00.5] word0" in out
