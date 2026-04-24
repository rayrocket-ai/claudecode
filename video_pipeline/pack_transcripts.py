#!/usr/bin/env python3
"""Pack word-level transcripts into phrase-level markdown.

Walks every `.words.json` under <edit-dir> (or a glob you provide) and emits
`takes_packed.md` — the primary reading artifact for cut selection.

Phrases break on:
  - silence >= --silence-threshold (default 0.5s), OR
  - speaker change (if speaker IDs are present)

Each phrase is prefixed with [start-end] so the editor can reference it
directly in an EDL.

Usage:
    python pack_transcripts.py --edit-dir <dir>
    python pack_transcripts.py --glob 'output/**/cleaned.words.json'
"""
from __future__ import annotations

import argparse
import glob as glob_mod
import json
import sys
from pathlib import Path


def format_time(s: float) -> str:
    return f"{s:06.2f}"


def format_duration(s: float) -> str:
    if s < 60:
        return f"{s:.1f}s"
    m = int(s // 60)
    return f"{m}m {s - m*60:04.1f}s"


def group_phrases(
    words: list[dict],
    silence_threshold: float,
) -> list[dict]:
    phrases: list[dict] = []
    buf: list[dict] = []
    speaker = None
    prev_end = None

    def flush() -> None:
        nonlocal buf, speaker
        if not buf:
            return
        text = " ".join(w["word"].strip() for w in buf if w["word"].strip())
        text = (text.replace(" ,", ",").replace(" .", ".")
                    .replace(" ?", "?").replace(" !", "!"))
        if text:
            phrases.append({
                "start": buf[0]["start"],
                "end": buf[-1]["end"],
                "text": text,
                "speaker": speaker,
            })
        buf = []
        speaker = None

    for w in words:
        sp = w.get("speaker")
        start = w.get("start")
        end = w.get("end", start)
        if start is None:
            continue
        if speaker is not None and sp is not None and sp != speaker:
            flush()
        if prev_end is not None and start - prev_end >= silence_threshold:
            flush()
        if not buf:
            speaker = sp
        buf.append(w)
        prev_end = end
    flush()
    return phrases


def pack_one(path: Path, silence_threshold: float) -> tuple[str, float, list[dict]]:
    words = json.loads(path.read_text())
    phrases = group_phrases(words, silence_threshold)
    dur = (phrases[-1]["end"] - phrases[0]["start"]) if phrases else 0.0
    # Use parent dir name if file is "cleaned.words.json", else file stem.
    if path.stem.endswith("cleaned"):
        name = path.parent.name
    else:
        name = path.stem.replace(".words", "")
    return name, dur, phrases


def render(entries: list[tuple[str, float, list[dict]]], threshold: float) -> str:
    out: list[str] = []
    out.append("# Packed transcripts")
    out.append("")
    out.append(f"Phrase-level, grouped on silences >= {threshold:.1f}s "
               f"or speaker change.")
    out.append("Use `[start-end]` ranges to address cuts in the EDL.")
    out.append("")
    for name, dur, phrases in entries:
        out.append(f"## {name}  (duration: {format_duration(dur)}, "
                   f"{len(phrases)} phrases)")
        if not phrases:
            out.append("  _no speech detected_")
            out.append("")
            continue
        for p in phrases:
            sp = p.get("speaker")
            sp_tag = ""
            if sp is not None:
                s = str(sp)
                if s.startswith("speaker_"):
                    s = s[len("speaker_"):]
                sp_tag = f" S{s}"
            out.append(
                f"  [{format_time(p['start'])}-{format_time(p['end'])}]"
                f"{sp_tag} {p['text']}"
            )
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit-dir", type=Path, default=None)
    ap.add_argument("--glob", default=None,
                    help="Glob for .words.json files (repo-relative)")
    ap.add_argument("--silence-threshold", type=float, default=0.5)
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()

    files: list[Path]
    if args.edit_dir:
        files = sorted(args.edit_dir.rglob("*.words.json"))
    elif args.glob:
        files = [Path(p) for p in sorted(glob_mod.glob(args.glob, recursive=True))]
    else:
        sys.exit("need --edit-dir or --glob")

    if not files:
        sys.exit("no .words.json files found")

    entries = [pack_one(p, args.silence_threshold) for p in files]
    md = render(entries, args.silence_threshold)

    out_path = args.output
    if out_path is None:
        out_path = (args.edit_dir or Path.cwd()) / "takes_packed.md"
    out_path.write_text(md)

    total = sum(len(e[2]) for e in entries)
    dur = sum(e[1] for e in entries)
    print(f"packed {len(entries)} files -> {out_path}")
    print(f"  {total} phrases, {format_duration(dur)} runtime, "
          f"{out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
