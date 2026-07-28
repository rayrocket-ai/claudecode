# ReelForge

A self-hosted agentic video editor. Give it long-form footage; get back ranked
vertical reels and finished YouTube episodes — trimmed, de-duplicated, captioned,
zoomed, and scored, with every editorial decision written down where you can
argue with it.

Runs on your own server. Your footage never leaves it.

## The idea

**The EDL is the product; the MP4 is a build artifact.**

Every editorial decision — each cut, zoom, caption, emoji, transition — is
written to a reviewable, diffable JSON edit decision list. Rendering is a pure
function of `(source, EDL)`.

That one choice buys four things:

- **Edits you can argue with.** "Why did you cut there?" has an answer in the file.
- **Reproducible renders.** Same EDL, same bytes out. Re-render at any resolution.
- **Tests without ffmpeg.** Editorial logic is validated against golden EDLs in CI.
- **Something to learn from.** Diffing what the brain proposed against what you
  accepted is the only signal a system can actually improve on.

That last one is why this exists rather than being an install of something else.
See [docs/TOOL-COMPARISON.md](docs/TOOL-COMPARISON.md) for the survey of
OpenMontage, video-use, HyperFrames, Remotion, Higgsfield and Descript, and what
each one is missing.

## Pipeline

```
inbox/ ──watcher──► ingest → analyse ──► BRAIN → EDL → render → QC ──► outbox/
        (automatic, cached)                ▲                     │
                                           └── memory/playbook ◄─┘ ── /reel-feedback
```

The **watcher** pre-warms the slow deterministic half the moment a file lands —
probe, audio extract, transcribe, silence/scene/energy/face analysis — throttled
so it never starves the rest of the box. By the time you SSH in, an hour-long
source is already transcribed and planning is instant.

The **brain** reads a timestamped transcript, a filmstrip contact sheet, and
cheap signal summaries — never raw frames — and emits hook candidates, story
beats, repeated takes, filler spans, emotional peaks, and clip scores.

The **composer** turns those into an EDL under deterministic craft rules
(minimum shot length, breath padding, zoom cadence, safe areas, emoji ceiling)
read from `memory/playbook.md`. That file is the seam where learning enters the
render.

**QC** samples frames either side of every cut and checks for visual jumps,
audio pops, caption overflow, orphaned words, black frames, and loudness drift —
then repairs the EDL and re-renders, up to three attempts.

## Status

| Phase | | |
|---|---|---|
| 0 | Scaffold, tool comparison, `/reel-doctor`, installer | **done** |
| 1 | Hetzner bring-up: watcher, systemd, Syncthing, retention | **done** |
| 2 | Ingest, analyse, WhisperX adapter, content-hash cache | **done** |
| 3 | EDL schema, parallel ffmpeg renderer, ASS captions, emoji | **done** |
| 4 | The brain + `/reels` end to end | **done** |
| 5 | `/vlog` — chapters, b-roll slots, music, metadata, thumbnails | **done** |
| 6 | QC self-eval loop with auto-repair | **done** |
| 7 | Premium overlays — Remotion **and** HyperFrames backends | |
| 8 | `memory/`, `/reel-feedback` — the learning loop | **done** |
| 9 | MCP server + LibreChat front end — edit from any browser | |
| 10 | Open-Generative-AI adapter — b-roll, intros, thumbnails | |

## Install

```bash
git clone https://github.com/rayrocket-ai/claudecode
cd claudecode/reelforge
./scripts/install.sh          # ffmpeg, faster-whisper, fonts, python env
./scripts/server-setup.sh     # server mode: inbox, systemd, Syncthing, tmux
cp config.example.toml config.toml
```

Then from Claude Code, `/reel-doctor` to verify.

See [docs/SERVER-RUNBOOK.md](docs/SERVER-RUNBOOK.md) for the Hetzner setup,
including how to reach it from a phone.

## Design notes worth knowing

**Emoji render as PNG overlays, not ASS glyphs.** libass colour-emoji support
depends on fontconfig in ways that fail silently on headless Linux — which is
exactly what a server is. Rasterising to PNG is deterministic and lets us
animate them.

**Auto-reframe uses per-span crop centres, not per-frame tracking.** Per-frame
face tracking jitters. A median focus point per span, eased between spans, reads
as intentional camera work.

**Segments render in parallel, then concat.** On a CPU-only box this is the
single biggest speed win available, far more than encoder tuning.

**Hardware is detected, never assumed.** `core/hardware.py` picks the whisper
model, compute type, parallelism and encoder. Moving to a GPU box later changes
speed, not code.

**`core/` is a library; every front end is a thin wrapper.** Slash commands, the
MCP server, and the watcher all call the same functions. That is what lets you
drive the same editor from Claude Code over SSH, from a LibreChat browser tab on
your phone, or unattended from the inbox — without three implementations of the
truth.

## Layout

```
commands/    slash commands (/reels, /vlog, /reel-doctor, /reel-feedback, /reel-bakeoff)
agents/      subagents: editor (the brain), colorist (framing), critic (QC)
skills/      ffmpeg recipes, caption styles, platform specs
core/        the engine: ingest, analyse, compose, render, qc, hardware
server/      inbox watcher, systemd units, retention
schema/      edl.schema.json -- the contract
remotion/    premium overlay compositions
memory/      style profile, playbook, decision log -- your taste, persisted
evals/       fixtures and golden EDLs
```
