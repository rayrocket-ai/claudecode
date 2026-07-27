# Why ReelForge exists: the landscape, July 2026

Before writing a line of ReelForge, we evaluated everything credible for doing
video work from a coding agent. This document records what we found, what we
took from each, and why we still built our own core.

Star counts are from GitHub search on 2026-07-27 and will drift.

## The contenders

### OpenMontage — `calesthio/OpenMontage` — 42.6k stars

A full agentic video production system: 12 pipelines, 100+ Python tools, 700+
skill and knowledge files. Integrates into coding agents through instruction
files rather than a plugin or MCP — you clone it, `make setup`, and tell your
agent what you want. Requires Python 3.10+, FFmpeg, Node 18+, with optional API
keys for Veo, Kling, Runway, FLUX, ElevenLabs, Suno and others.

It has a **Clip Factory** pipeline that does roughly what we want: "batch of
ranked short-form clips from one long source."

**Why we didn't fork it.** Its center of gravity is *generating* video from
prompts, not surgically editing footage you already shot. Adopting it means
owning a very large codebase optimised for a different job, and every taste
change means fighting an architecture built around someone else's workflow.

**What we took.** The clip-ranking framing, and the "stage director" pattern —
per-stage skill files that teach the agent exactly how to execute one phase,
rather than one enormous prompt.

### video-use — `browser-use/video-use` — 17.9k stars

The closest existing thing to what you asked for. Drop footage in a folder, chat
with the agent, get `final.mp4`. Pipeline: transcription → packing → LLM
reasoning → edit decision list → render → self-evaluation. It reads video as
timestamped text plus on-demand filmstrip/waveform composites rather than
dumping frames, which keeps token cost sane. Cuts filler words and dead space at
word boundaries, colour grades, fades audio at cuts, burns subtitles.

**Why we didn't wrap it.** It is deliberately scoped to *cutting and audio
cleanup*. Zooms, clip ranking, emoji, animation, platform reframing, and any
notion of learned taste are all absent — and that is the majority of what makes
a reel look professional rather than merely trimmed.

**What we took.** The architecture, essentially wholesale: an EDL as the
intermediate representation, text-first video comprehension, and a self-eval
loop that re-renders when QC fails. These are the right primitives.

### HyperFrames — `heygen-com/hyperframes` — 38.0k stars

HTML/CSS + GSAP/Lottie/Three.js rendered deterministically to MP4 via headless
Chrome and FFmpeg. Installs as an agent skill (`npx skills add
heygen-com/hyperframes`). Apache 2.0. "Same input, same frames, same output."

**Where it fits.** It creates new motion graphics; it does not edit existing
footage. It *can* composite over background video, so it is a legitimate overlay
engine.

**Why Remotion won that slot.** Only on ecosystem maturity — Remotion's official
agent skill is far more thoroughly documented, which matters when the agent is
the one writing the compositions. HyperFrames remains a drop-in alternative and
the renderer interface is written so it could be swapped.

### Remotion + official agent skill

React → video, with an official 28-file agent skill covering component patterns,
transitions, spring physics, interpolation, and audio timing. Roughly 126k
installs; reported as the #4 most-installed agent skill overall and the most
popular for programmatic video.

**Where it fits.** ReelForge's *premium overlay tier*. Remotion never touches
base footage — it renders animated overlays (lower thirds, kinetic type,
counters) as a transparent layer that FFmpeg composites on top. That keeps it
opt-in per overlay and cheap even on a CPU-only box, because it is only ever
rendering short transparent clips, not full frames.

### Higgsfield MCP

Hosted, already connected in our environment: `shorts_studio`,
`personal_clipper`, `video_analysis`, `virality_predictor`, `reframe`,
`upscale_video`, `dubbing`.

**Where it fits.** An *outside opinion*, not the engine. `virality_predictor`
scoring our clip candidates is a genuinely useful independent check on our own
ranking, and `/reel-bakeoff` uses it that way. Using it as the editor would mean
renting taste we cannot inspect or tune.

### Descript MCP

Descript's official hosted MCP (`api.descript.com/v2/mcp`, OAuth) exposes the
Underlord editor: import media, run edits, manage compositions, publish. Handles
"pull three social clips from this podcast" natively.

**Why not.** Three disqualifiers for this project: the editing brain is not
tunable, it bills per video, and your footage uploads to a third party — which
defeats the point of self-hosting. Retained as an optional *export* target.

### Claude Code Video Toolkit — `wilwaldon/Claude-Code-Video-Toolkit`

A curated bundle of skills and MCP servers covering Remotion, Manim, screen
recording, YouTube clipping, and FFmpeg post-processing. Useful as a reference
for FFmpeg recipes. Not an editorial system.

## Adopted alongside the core

These three are not editors and were never competing for the core slot. Each
fills a real gap around it, and all three are self-hostable — which is the whole
premise.

### LibreChat — `danny-avila/LibreChat` — the front end

Self-hosted ChatGPT-style UI with first-class **agents, MCP support**, artifacts,
conversation search, and multi-user auth. Deploys via Docker Compose behind a
reverse proxy.

**Why it matters here.** SSH + tmux genuinely works from anywhere, but typing
editorial direction into a terminal on a phone is unpleasant — fine for "3 reels,
punchy hook", miserable for a real conversation about pacing. LibreChat solves
that properly: ReelForge exposes itself as an **MCP server**, a LibreChat agent
on the tailnet consumes it, and you edit from a browser on any device with
video previews inline.

This supersedes the Telegram front-end that was previously sketched as a later
phase. Same benefit, no bot to build, and it does not recompress your footage.

**Design consequence, and the reason this was worth catching early:** the core
must expose a clean programmatic API, not just slash commands. `commands/` and
the MCP server both become thin wrappers over the same functions in `core/`.

### Open-Generative-AI — `Anil-matcha/Open-Generative-AI` — 25.0k stars — asset generation

Self-hosted studio front-end for image and video generation across 500+ models
(Flux, Kling, Sora, Veo, lipsync). MIT licensed.

**Where it fits.** Not editing — *generation*. It fills the asset-shaped holes an
editor leaves behind: b-roll for `/vlog` slots, intro and outro animations,
thumbnail variants, and background plates. ReelForge marks a slot in the EDL;
this fills it.

**Honest caveat.** "Self-hosted" here means the *studio UI* is self-hosted; the
models themselves are largely hosted APIs behind aggregators, so it needs keys
and credits and does send prompts out. It is not free-and-local the way our
transcription and rendering are. Generated assets are cached locally once
fetched, and the whole adapter is optional — `/vlog` leaves marked b-roll slots
for you to fill manually when it is disabled.

### HyperFrames — promoted to a supported overlay backend

Originally evaluated as the losing alternative to Remotion. Promoted: both are
now supported behind one `OverlayRenderer` interface, selectable per composition.

They have genuinely different strengths. Remotion has the deeper agent skill and
better docs, so the agent writes correct React compositions more reliably.
HyperFrames is plain HTML/CSS/GSAP with no build step, which makes it faster to
author, easier to debug by opening the file in a browser, and lighter on a
CPU-only box. Kinetic typography and quick lower-thirds go to HyperFrames;
anything needing spring physics or complex sequencing goes to Remotion.

## The gap

| Capability | OpenMontage | video-use | HyperFrames | Remotion | Higgsfield | Descript | **ReelForge** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Cuts your own footage | ✓ | ✓ | — | — | ✓ | ✓ | ✓ |
| Word-level filler / retake removal | ~ | ✓ | — | — | ~ | ✓ | ✓ |
| Ranks clips from a long source | ✓ | — | — | — | ✓ | ✓ | ✓ |
| Auto reframe 16:9 → 9:16 | ~ | — | — | — | ✓ | ✓ | ✓ |
| Punch-in zooms / transitions | ~ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Word-level captions + emoji | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Animated overlays | ✓ | — | ✓ | ✓ | ~ | ~ | ✓ |
| Self-evaluating QC loop | — | ✓ | — | — | — | — | ✓ |
| Runs fully self-hosted, no upload | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| **Persistent, improving taste** | — | — | — | — | — | — | **✓** |

The bottom row is the one that does not exist anywhere else, and it is the
reason we own the core rather than installing someone else's.

## The design consequence

**The EDL is the product; the MP4 is a build artifact.**

Every editorial decision is written to a reviewable, diffable JSON edit decision
list, and rendering is a pure function of `(source, EDL)`. That gives us four
things at once: edits you can argue with, renders you can reproduce at any
resolution, tests that run without FFmpeg installed, and — the point — a record
of what the brain proposed versus what you accepted, which is the only thing a
system can actually learn from.

## Reproducing this comparison

```bash
# Star counts and activity
gh search repos 'video editing agent ffmpeg' --sort stars --limit 20
```

Or from Claude Code with the GitHub MCP server:
`search_repositories(query="video editing agent ffmpeg in:name,description,readme stars:>500", sort="stars")`

Sources:
- <https://github.com/calesthio/OpenMontage>
- <https://github.com/browser-use/video-use>
- <https://github.com/heygen-com/hyperframes>
- <https://www.remotion.dev/docs/ai/skills>
- <https://help.descript.com/hc/en-us/articles/46056322186509-Descript-MCP-overview>
- <https://higgsfield.ai/blog/Generate-AI-Videos-From-Claude-with-Higgsfield-MCP>
- <https://github.com/wilwaldon/Claude-Code-Video-Toolkit>
