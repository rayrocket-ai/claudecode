#!/usr/bin/env python3
"""Remove filler words and stutters from a video using word-level timestamps.

Reads <input>.words.json produced by transcribe.py, finds filler tokens and
stutters, then cuts them out via per-segment extract + lossless concat.

Usage:
    python cut_fillers.py <input_video> <output_video> \\
        [--words PATH] [--pad 0.05] [--cut-discourse] [--dry-run]

--pad             Seconds to pad on each side of a filler before cutting.
                  0.05 (50ms) is safe; reduce to 0.02 for tight cuts.
--cut-discourse   Also cut "like / you know / I mean / sort of / basically"
                  (off by default — preserves natural cadence).
--dry-run         Print the cut list without producing a file.

Snaps every cut edge to the nearest word boundary to satisfy the
editorial contract in .claude/skills/video-editing/SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


# Always-cut fillers (hesitation tokens that carry no editorial signal).
CORE_FILLERS = {
    "um", "uhm", "umm", "ummm",
    "uh", "uhh", "uhhh",
    "er", "err", "erm",
    "ah", "ahh",
    "hmm", "hm", "mm", "mhm",
    "eh",
}

# Discourse markers — cut only with --cut-discourse.
DISCOURSE_MARKERS = {
    "like", "basically", "literally", "actually", "honestly",
    "seriously", "obviously", "right",
}

# Multi-word discourse phrases.
DISCOURSE_PHRASES = [
    ("you", "know"),
    ("i", "mean"),
    ("sort", "of"),
    ("kind", "of"),
    ("you", "see"),
]


def normalize(token: str) -> str:
    """Lowercase and strip punctuation/whitespace."""
    return re.sub(r"[^a-z']+", "", token.lower())


def find_filler_indices(
    words: list[dict],
    cut_discourse: bool,
) -> set[int]:
    """Return indices in `words` that should be removed."""
    cut: set[int] = set()
    normed = [normalize(w["word"]) for w in words]

    # Core fillers.
    for i, n in enumerate(normed):
        if n in CORE_FILLERS:
            cut.add(i)

    # Stutters: consecutive identical tokens, collapse all but the last.
    # Also "I-I", "the-the" style where the first is a fragment of the second.
    for i in range(len(normed) - 1):
        a, b = normed[i], normed[i + 1]
        if not a or not b:
            continue
        if a == b:
            cut.add(i)
        elif len(a) <= 2 and b.startswith(a) and a != b:
            # "I" → "I-I" or "th" → "the"
            cut.add(i)

    # Discourse markers + phrases.
    if cut_discourse:
        for i, n in enumerate(normed):
            if n in DISCOURSE_MARKERS:
                cut.add(i)
        for i in range(len(normed) - 1):
            pair = (normed[i], normed[i + 1])
            if pair in DISCOURSE_PHRASES:
                cut.add(i)
                cut.add(i + 1)

    return cut


def build_keep_ranges(
    words: list[dict],
    cut_indices: set[int],
    duration: float,
    pad: float,
) -> list[tuple[float, float]]:
    """Collapse cuts into keep-ranges over the timeline.

    Rule: start at 0, walk forward. When we hit a run of cut indices,
    stop the current keep range at (word.start - pad) and resume at
    (last_cut_word.end + pad).
    """
    keep: list[tuple[float, float]] = []
    cursor = 0.0
    i = 0
    n = len(words)
    while i < n:
        if i in cut_indices:
            # End current keep at the cut start.
            cut_start = max(cursor, words[i]["start"] - pad)
            # Advance through the run of cut indices.
            j = i
            while j < n and j in cut_indices:
                j += 1
            cut_end_time = words[j - 1]["end"] + pad
            if cut_start > cursor:
                keep.append((cursor, cut_start))
            cursor = cut_end_time
            i = j
        else:
            i += 1
    if cursor < duration:
        keep.append((cursor, duration))
    return keep


def get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def build_filtergraph(keep: list[tuple[float, float]], fade: float = 0.03) -> str:
    """Per-segment trim + 30ms afade in/out on each segment, then concat."""
    parts = []
    for i, (s, e) in enumerate(keep):
        dur = e - s
        parts.append(
            f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade},"
            f"afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade}[a{i}]"
        )
    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(keep)))
    return ";".join(parts) + f";{concat_inputs}concat=n={len(keep)}:v=1:a=1[v][a]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--words", default=None,
                    help="Path to .words.json (defaults to <input>.words.json)")
    ap.add_argument("--pad", type=float, default=0.05)
    ap.add_argument("--cut-discourse", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    if args.words:
        words_path = Path(args.words).resolve()
    else:
        words_path = Path(str(in_path.with_suffix("")) + ".words.json")
    if not words_path.exists():
        print(f"Missing {words_path}. Run transcribe.py first.", file=sys.stderr)
        sys.exit(1)

    words = json.loads(words_path.read_text())
    if not words:
        print("words.json is empty; nothing to cut.", file=sys.stderr)
        sys.exit(1)

    duration = get_duration(str(in_path))
    cut_idx = find_filler_indices(words, args.cut_discourse)

    if not cut_idx:
        print("No fillers found.")
        if not args.dry_run:
            # Nothing to cut — just copy.
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(in_path), "-c", "copy", str(out_path)],
                check=True,
            )
        return

    keep = build_keep_ranges(words, cut_idx, duration, args.pad)
    kept = sum(e - s for s, e in keep)
    print(f"Fillers found: {len(cut_idx)} tokens")
    print(f"Keep ranges: {len(keep)} (kept {kept:.2f}s / cut {duration - kept:.2f}s)")

    if args.dry_run:
        for i, (s, e) in enumerate(keep):
            print(f"  keep [{i:02d}] {s:7.2f} -> {e:7.2f}  ({e - s:5.2f}s)")
        # Show first 20 cut words for sanity check.
        sample = sorted(cut_idx)[:20]
        print("\nFirst cuts:")
        for i in sample:
            w = words[i]
            print(f"  {w['start']:7.2f}-{w['end']:7.2f}  {w['word']!r}")
        return

    if not keep:
        print("Nothing to keep after cuts. Aborting.", file=sys.stderr)
        sys.exit(1)

    filter_complex = build_filtergraph(keep)
    cmd = [
        "ffmpeg", "-y", "-i", str(in_path),
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path),
    ]
    print("Running ffmpeg...")
    subprocess.run(cmd, check=True)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
