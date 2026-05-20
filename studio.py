#!/usr/bin/env python3
"""Studio — one entry point for the video editing pipeline.

Subcommands:
    studio.py prep     <input.mp4> [--engine scribe|whisper] [--model base]
    studio.py render   <edl.json>  -o out.mp4 [--preview]
    studio.py pack     <edit-dir>
    studio.py releases [--limit 10]
    studio.py pull     [TAG | --latest] [--prep]

Example full pipeline, from raw camera file to a production MP4:

    python studio.py pull --latest --prep              # grab newest upload, prep it
    # edit edl.json by hand or via an agent using .claude/skills/video-editing/SKILL.md
    python studio.py render edl.json -o output/final.mp4

`prep` runs: silence cut -> transcribe -> filler cut -> re-transcribe -> pack.
`pull` reads from GitHub releases tagged `raw-*` (uploaded by
scripts/watch_and_upload.sh running on your laptop).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PIPELINE = ROOT / "video_pipeline"
DEFAULT_REPO = os.environ.get("GITHUB_REPO", "rayrocket-ai/claudecode")
GITHUB_API = "https://api.github.com"


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)


def cmd_prep(args: argparse.Namespace) -> None:
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        sys.exit(f"Input not found: {in_path}")

    basename = in_path.stem
    out_dir = PIPELINE / "output" / basename
    out_dir.mkdir(parents=True, exist_ok=True)

    silenced = out_dir / "silenced.mp4"
    cleaned = out_dir / "cleaned.mp4"

    print("=== [1/5] Cutting silence ===")
    run(["python3", str(PIPELINE / "cut_silence.py"), str(in_path), str(silenced)])

    print("=== [2/5] Transcribing (pre-filler) ===")
    transcribe_cmd = ["python3", str(PIPELINE / "transcribe.py"), str(silenced)]
    if args.engine == "scribe":
        transcribe_cmd += ["--engine", "scribe"]
    else:
        transcribe_cmd += ["--engine", "whisper", "--model", args.model]
    run(transcribe_cmd)

    print("=== [3/5] Cutting fillers ===")
    filler_cmd = ["python3", str(PIPELINE / "cut_fillers.py"), str(silenced), str(cleaned)]
    if args.cut_discourse:
        filler_cmd.append("--cut-discourse")
    run(filler_cmd)

    print("=== [4/5] Re-transcribing cleaned cut ===")
    retranscribe_cmd = ["python3", str(PIPELINE / "transcribe.py"), str(cleaned)]
    if args.engine == "scribe":
        retranscribe_cmd += ["--engine", "scribe"]
    else:
        retranscribe_cmd += ["--engine", "whisper", "--model", args.model]
    run(retranscribe_cmd)

    print("=== [5/5] Packing phrase-level markdown ===")
    run(
        ["python3", str(PIPELINE / "pack_transcripts.py"),
         "--glob", str(out_dir / "cleaned.words.json"),
         "-o", str(out_dir / "takes_packed.md")],
    )

    print()
    print(f"Done. Artifacts in: {out_dir}")
    print(f"  - {silenced.name}            (silence removed)")
    print(f"  - {cleaned.name}             (silence + fillers removed)")
    print(f"  - cleaned.words.json  (word-level timings)")
    print(f"  - cleaned.srt         (subtitles)")
    print(f"  - takes_packed.md     (phrase-level reading artifact)")
    print()
    print("Next:")
    print("  - Draft an EDL (see .claude/skills/video-editing/SKILL.md)")
    print(f"  - python3 studio.py render edl.json -o {out_dir}/final.mp4")
    print("  - Or open in Remotion: cd video_remotion && npm run start")


def cmd_render(args: argparse.Namespace) -> None:
    cmd = ["python3", str(PIPELINE / "render.py"), args.edl, "-o", args.output]
    if args.preview:
        cmd.append("--preview")
    if args.no_loudnorm:
        cmd.append("--no-loudnorm")
    run(cmd)


def cmd_pack(args: argparse.Namespace) -> None:
    run(
        ["python3", str(PIPELINE / "pack_transcripts.py"),
         "--edit-dir", str(Path(args.edit_dir).resolve())],
    )


# ---------- GitHub release helpers ----------

def _load_env() -> None:
    """Load GITHUB_TOKEN from .env if present."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _gh_request(path: str, *, accept: str = "application/vnd.github+json",
                binary: bool = False) -> bytes | dict:
    """GET against api.github.com. Authenticated if GITHUB_TOKEN is set."""
    _load_env()
    url = f"{GITHUB_API}{path}" if path.startswith("/") else path
    req = urllib.request.Request(url)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "claudecode-studio/1.0")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:400]
        sys.exit(f"GitHub API {e.code}: {body}")
    return data if binary else json.loads(data)


def _list_raw_releases(repo: str, limit: int) -> list[dict]:
    """Return releases tagged `raw-*`, newest first."""
    releases = _gh_request(f"/repos/{repo}/releases?per_page={min(100, limit * 2)}")
    raw = [r for r in releases if r.get("tag_name", "").startswith("raw-")]
    return raw[:limit]


def _download_asset(asset: dict, dest_dir: Path) -> Path:
    """Stream a release asset to dest_dir. Returns the path."""
    name = asset["name"]
    out = dest_dir / name
    _load_env()
    # api.github.com URL with Accept: octet-stream for authenticated download.
    url = asset["url"]
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/octet-stream")
    req.add_header("User-Agent", "claudecode-studio/1.0")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=600) as r, out.open("wb") as f:
            total = int(r.headers.get("Content-Length", 0))
            done = 0
            chunk_size = 1 << 20  # 1 MiB
            while True:
                chunk = r.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 / total
                    sys.stdout.write(f"\r  {name}: {done / (1<<20):.1f} / "
                                     f"{total / (1<<20):.1f} MiB ({pct:.0f}%)")
                    sys.stdout.flush()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:400]
        sys.exit(f"\nasset download {e.code}: {body}")
    sys.stdout.write("\n")
    return out


def cmd_releases(args: argparse.Namespace) -> None:
    releases = _list_raw_releases(args.repo, args.limit)
    if not releases:
        print(f"No raw-* releases in {args.repo}.")
        return
    print(f"{'TAG':<40} {'TITLE':<40} {'ASSETS':<6}")
    for r in releases:
        n_assets = len(r.get("assets", []))
        title = (r.get("name") or "")[:38]
        print(f"{r['tag_name']:<40} {title:<40} {n_assets:<6}")


def cmd_pull(args: argparse.Namespace) -> None:
    input_dir = PIPELINE / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    if args.tag and args.latest:
        sys.exit("Pass either a TAG or --latest, not both.")

    if args.latest or not args.tag:
        releases = _list_raw_releases(args.repo, 1)
        if not releases:
            sys.exit(f"No raw-* releases in {args.repo}.")
        release = releases[0]
    else:
        release = _gh_request(f"/repos/{args.repo}/releases/tags/{args.tag}")

    assets = release.get("assets", [])
    if not assets:
        sys.exit(f"Release {release['tag_name']} has no assets.")

    print(f"pulling {release['tag_name']}  ({len(assets)} asset{'s' if len(assets) > 1 else ''})")
    downloaded: list[Path] = []
    for a in assets:
        # Skip non-video files (e.g. checksums) — keep it tidy.
        if "/" not in a.get("content_type", "") and not a["name"].lower().endswith(
            (".mp4", ".mov", ".m4v", ".webm", ".mkv")
        ):
            print(f"  skip non-video: {a['name']}")
            continue
        path = _download_asset(a, input_dir)
        downloaded.append(path)
        print(f"  wrote {path}")

    if not downloaded:
        sys.exit("nothing downloaded.")

    if args.prep:
        # Run prep on each downloaded file.
        for path in downloaded:
            print(f"\n=== prepping {path.name} ===")
            prep_cmd = ["python3", str(ROOT / "studio.py"), "prep", str(path)]
            if args.engine:
                prep_cmd += ["--engine", args.engine]
            if args.model:
                prep_cmd += ["--model", args.model]
            if args.cut_discourse:
                prep_cmd.append("--cut-discourse")
            run(prep_cmd)


def main() -> None:
    ap = argparse.ArgumentParser(description="Video editing studio entry point")
    subs = ap.add_subparsers(dest="command", required=True)

    p = subs.add_parser("prep", help="transcribe, cut silence + fillers, pack")
    p.add_argument("input")
    p.add_argument("--engine", choices=["whisper", "scribe"], default="whisper")
    p.add_argument("--model", default="base",
                   help="Whisper model size (whisper engine only)")
    p.add_argument("--cut-discourse", action="store_true",
                   help="Also cut like/you know/I mean/sort of")
    p.set_defaults(func=cmd_prep)

    p = subs.add_parser("render", help="render an EDL to final MP4")
    p.add_argument("edl")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--preview", action="store_true")
    p.add_argument("--no-loudnorm", action="store_true")
    p.set_defaults(func=cmd_render)

    p = subs.add_parser("pack", help="pack transcripts into takes_packed.md")
    p.add_argument("edit_dir")
    p.set_defaults(func=cmd_pack)

    p = subs.add_parser("releases", help="list recent raw-* releases")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_releases)

    p = subs.add_parser("pull",
        help="download a raw-* release asset into video_pipeline/input/")
    p.add_argument("tag", nargs="?", default=None,
                   help="Release tag (e.g. raw-20260520-104133-clip). "
                        "Omit and pass --latest to grab newest.")
    p.add_argument("--latest", action="store_true",
                   help="Pick the newest raw-* release")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--prep", action="store_true",
                   help="After downloading, run `studio.py prep` on the file")
    p.add_argument("--engine", choices=["whisper", "scribe"], default=None,
                   help="Passed through to prep")
    p.add_argument("--model", default=None,
                   help="Passed through to prep")
    p.add_argument("--cut-discourse", action="store_true",
                   help="Passed through to prep")
    p.set_defaults(func=cmd_pull)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
