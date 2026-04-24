#!/usr/bin/env python3
"""Transcribe a video/audio file to SRT with word-level timings.

Two engines:
  whisper  (default, free, local)  — faster-whisper. Normalizes fillers away.
  scribe   (paid, remote)          — ElevenLabs Scribe. Keeps fillers + speakers.

Usage:
    python transcribe.py <input> [--engine whisper|scribe] [--model base] \\
        [--lang en] [--speakers N] [--force]

Outputs next to the input:
    <name>.srt              -- subtitle file (output-timeline, word-group captions)
    <name>.words.json       -- word-level timings (feeds cut_fillers.py, Remotion)
    <name>.segments.json    -- segment/phrase-level timings
    <name>.scribe.json      -- raw Scribe response (scribe engine only, cached)

Caching: scribe runs are cached per source-file hash. Pass --force to re-run.
Env: ELEVENLABS_API_KEY must be set (or in .env at repo root) for scribe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


# ---------- shared helpers ----------

def format_ts(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_outputs(
    stem: Path,
    words: list[dict],
    segments: list[dict],
) -> None:
    srt_path = Path(str(stem) + ".srt")
    words_path = Path(str(stem) + ".words.json")
    segs_path = Path(str(stem) + ".segments.json")

    srt_lines = []
    for idx, seg in enumerate(segments, 1):
        srt_lines.append(str(idx))
        srt_lines.append(f"{format_ts(seg['start'])} --> {format_ts(seg['end'])}")
        srt_lines.append(seg["text"].strip())
        srt_lines.append("")
    srt_path.write_text("\n".join(srt_lines))
    words_path.write_text(json.dumps(words, indent=2))
    segs_path.write_text(json.dumps(segments, indent=2))

    print(f"Wrote: {srt_path.name}")
    print(f"Wrote: {words_path.name}  ({len(words)} words)")
    print(f"Wrote: {segs_path.name}  ({len(segments)} segments)")


def file_hash(path: Path) -> str:
    h = hashlib.sha1()
    h.update(str(path.stat().st_size).encode())
    with path.open("rb") as f:
        h.update(f.read(1 << 20))  # first 1 MB is enough as an identity check
    return h.hexdigest()[:16]


# ---------- whisper engine ----------

def run_whisper(
    in_path: Path,
    stem: Path,
    model_name: str,
    lang: str | None,
    device: str,
) -> None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper not installed. pip install -r requirements.txt",
              file=sys.stderr)
        sys.exit(1)

    print(f"[whisper] loading model: {model_name}")
    model = WhisperModel(model_name, device=device, compute_type="int8")
    print(f"[whisper] transcribing {in_path.name}")
    segments_iter, info = model.transcribe(
        str(in_path),
        language=lang,
        word_timestamps=True,
        vad_filter=True,
    )

    words: list[dict] = []
    segments: list[dict] = []
    for seg in segments_iter:
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "prob": w.probability,
                })
    print(f"[whisper] detected language: {info.language} "
          f"(prob {info.language_probability:.2f})")
    write_outputs(stem, words, segments)


# ---------- scribe engine ----------

def load_env() -> None:
    """Load .env from repo root if present (no dependency on python-dotenv)."""
    for candidate in [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def run_scribe(
    in_path: Path,
    stem: Path,
    lang: str | None,
    speakers: int | None,
    force: bool,
) -> None:
    import httpx  # already in root requirements

    load_env()
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        print("ELEVENLABS_API_KEY is not set. Add it to your .env.",
              file=sys.stderr)
        sys.exit(1)

    cache_path = Path(str(stem) + ".scribe.json")
    hash_marker = Path(str(stem) + f".scribe.{file_hash(in_path)}.ok")

    if cache_path.exists() and hash_marker.exists() and not force:
        print(f"[scribe] cache hit: {cache_path.name}")
        data = json.loads(cache_path.read_text())
    else:
        print(f"[scribe] uploading {in_path.name} to ElevenLabs")
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        data_form = {"model_id": "scribe_v1"}
        if lang:
            data_form["language_code"] = lang
        if speakers:
            data_form["num_speakers"] = str(speakers)
        with in_path.open("rb") as f:
            with httpx.Client(timeout=600.0) as client:
                r = client.post(
                    url,
                    headers={"xi-api-key": api_key},
                    data=data_form,
                    files={"file": (in_path.name, f, "application/octet-stream")},
                )
        if r.status_code != 200:
            print(f"[scribe] HTTP {r.status_code}: {r.text[:500]}", file=sys.stderr)
            sys.exit(1)
        data = r.json()
        cache_path.write_text(json.dumps(data, indent=2))
        # Clear any old marker, stamp the new one.
        for p in stem.parent.glob(f"{stem.name}.scribe.*.ok"):
            p.unlink()
        hash_marker.write_text("ok")
        print(f"[scribe] cached: {cache_path.name}")

    words_raw = data.get("words", [])
    words: list[dict] = []
    for w in words_raw:
        if w.get("type") != "word":
            continue
        if w.get("start") is None or w.get("end") is None:
            continue
        words.append({
            "word": w.get("text", ""),
            "start": float(w["start"]),
            "end": float(w["end"]),
            "speaker": w.get("speaker_id"),
        })

    # Phrase segmentation: break on silence gap >= 0.5s or speaker change.
    segments: list[dict] = []
    buf: list[dict] = []
    speaker = None
    prev_end = None
    for w in words_raw:
        if w.get("type") == "spacing":
            if prev_end is not None and w.get("end") is not None:
                gap = w["end"] - (w.get("start") or prev_end)
                if gap >= 0.5 and buf:
                    segments.append(_flush_segment(buf))
                    buf = []
                    speaker = None
            continue
        if w.get("type") not in ("word", "audio_event"):
            continue
        if w.get("start") is None:
            continue
        sp = w.get("speaker_id")
        if speaker is not None and sp is not None and sp != speaker and buf:
            segments.append(_flush_segment(buf))
            buf = []
        if not buf:
            speaker = sp
        buf.append(w)
        prev_end = w.get("end", w["start"])
    if buf:
        segments.append(_flush_segment(buf))

    write_outputs(stem, words, segments)


def _flush_segment(buf: list[dict]) -> dict:
    parts = []
    for w in buf:
        t = w.get("text", "").strip()
        if not t:
            continue
        if w.get("type") == "audio_event" and not t.startswith("("):
            t = f"({t})"
        parts.append(t)
    text = " ".join(parts)
    text = (text.replace(" ,", ",").replace(" .", ".")
                .replace(" ?", "?").replace(" !", "!"))
    return {
        "start": float(buf[0]["start"]),
        "end": float(buf[-1].get("end", buf[-1]["start"])),
        "text": text,
        "speaker_id": buf[0].get("speaker_id"),
    }


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--engine", choices=["whisper", "scribe"], default="whisper")
    ap.add_argument("--model", default="base",
                    help="Whisper model size (tiny|base|small|medium|large-v3)")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--device", default="cpu", help="whisper: cpu|cuda")
    ap.add_argument("--speakers", type=int, default=None,
                    help="scribe: hint number of speakers")
    ap.add_argument("--force", action="store_true",
                    help="scribe: bypass cache")
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    stem = in_path.with_suffix("")
    if args.engine == "scribe":
        run_scribe(in_path, stem, args.lang, args.speakers, args.force)
    else:
        run_whisper(in_path, stem, args.model, args.lang, args.device)


if __name__ == "__main__":
    main()
