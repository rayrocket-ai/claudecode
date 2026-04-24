---
name: video-editing
description: Editorial contract for this repo's video pipeline. Applies whenever you edit, cut, or compose video. Covers filler removal, cut rules, EDL format, overlay composition, subtitles, and which renderer to reach for (Remotion vs Hyperframes). Read this before touching any .mp4, .srt, .words.json, or EDL file.
---

# Video Editing Skill

You are editing video in a studio repo that has three tools wired up:

- `video_pipeline/` — Python + FFmpeg + faster-whisper / ElevenLabs Scribe. Does transcription, silence removal, filler removal, EDL rendering.
- `video_remotion/` — React/Remotion compositor. Owns captions, B-roll, title cards, motion-graphics overlays baked *with* the base video.
- `video_hyperframes/` — HTML/GSAP compositor (independent). Standalone motion-graphics inserts; outputs MP4/WebM (with alpha).

The user picks Remotion or Hyperframes per task. You do **not** cross-import between them.

## Non-negotiable hard rules

These are correctness rules, not style. Violating any of them produces broken video.

1. **Snap every cut edge to a word boundary.** Use timestamps from `.words.json`. Never cut mid-word. Scribe drifts 50–100ms; always pad 30–200ms on each edge.
2. **30ms audio fades at every segment boundary.** Use `afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03}:d=0.03`. Hard cuts cause audible pops.
3. **Per-segment extract + lossless concat**, not single-pass filtergraph. Extract each kept range to its own file with `-c:v libx264 -crf 20 -c:a aac`, then concat via the concat demuxer with `-c copy`. Double-encoding is forbidden.
4. **Overlays use PTS-shift.** `setpts=PTS-STARTPTS+{T}/TB` to align animation frame 0 with its window start in the output timeline.
5. **Subtitles are applied LAST.** After every overlay, color grade, and composite. Otherwise overlays hide captions.
6. **Output-timeline subtitle offsets.** `output_time = word.start - segment_start + segment_offset`. Never copy source-timeline timestamps into the master SRT.
7. **Verbatim ASR.** Prefer Scribe (`transcribe.py --engine scribe`) when fillers matter. faster-whisper normalizes fillers away and makes filler removal impossible.
8. **Cache transcripts.** Never re-transcribe a source file that hasn't changed. Key the cache on file hash + size.
9. **Parallel sub-agents for animations.** When rendering multiple overlays, spawn one sub-agent per overlay. Never sequential.
10. **Confirm strategy before cutting.** Propose a 4–8 sentence edit plan. Wait for the user's OK. Then cut.

## The editing loop

1. **Inventory.** For each source: `ffprobe` for duration/codec; transcribe with Scribe (or Whisper if the user opts for free/local). Cache transcripts under `<out>/transcripts/`.
2. **Pack.** Run `pack_transcripts.py --edit-dir <out>` to produce `takes_packed.md` — phrase-level markdown with `[start-end]` prefixes. This is the primary reading artifact.
3. **Propose.** In chat, lay out a 4–8 sentence plan: target length, structure archetype, rough beats, grade, subtitle style. Wait for OK.
4. **Cut.** Emit an EDL JSON (format below). Call `render.py <edl.json> -o out.mp4` to produce the final edit.
5. **Self-evaluate.** After render, ffprobe the output, sample frames at every cut boundary, confirm no glitches or missing audio.
6. **Iterate.** Accept natural-language feedback, amend the EDL, re-render. Persist each session to `project.md`.

## EDL format (the contract between agent and renderer)

```json
{
  "version": 1,
  "sources": {
    "A": "/abs/path/take1.mp4",
    "B": "/abs/path/take2.mp4"
  },
  "ranges": [
    {
      "source": "A",
      "start": 2.42,
      "end": 6.85,
      "beat": "HOOK",
      "quote": "Ninety percent of what a web agent does is wasted.",
      "reason": "Best delivery; eyes up at 4.1s"
    }
  ],
  "grade": "warm_cinematic",
  "audio_fade": 0.03,
  "overlays": [
    {
      "file": "overlays/slot_1.mov",
      "start_in_output": 0.0,
      "duration": 5.0,
      "x": "(W-w)/2",
      "y": "H*0.15"
    }
  ],
  "subtitles": "master.srt",
  "subtitle_style": "bold-overlay",
  "total_duration_s": 87.4
}
```

## Cut craft

- Silences ≥400ms are the safest cuts.
- 150–400ms phrase boundaries are usable with visual verification.
- <150ms is unsafe. Don't cut there.
- Filler words (`um`, `uh`, `er`, `ah`, `hmm`, `mhm`) always cut.
- Discourse markers (`like`, `you know`, `so`, `basically`, `I mean`, `sort of`) — cut by default, but preserve one or two for natural cadence.
- Stutters (`I-I-I`, `the the`, `we we`) — collapse to one instance.
- Audio events `(laughs)`, `(sighs)`, `(applause)` — editorial peaks. Extend cut past them.
- Speaker handoffs: 400–600ms of air between utterances. Tighter for fast-paced, looser for cinematic.

## Color grading

Think ASC CDL: `out = (in * slope + offset) ** power`, then global saturation. Apply per-segment during extraction, never post-concat. Presets in `render.py`:

- `warm_cinematic` — teal/orange split, desaturated. Tech/launch/retro.
- `neutral_punch` — contrast bump + S-curve. General-purpose.
- `none` — straight copy.

Test on skin tones before committing to anything aggressive.

## Subtitles

- **`bold-overlay`** — 2-word chunks, UPPERCASE, break on punctuation, Helvetica 18 Bold, white with outline, `MarginV=35`. For short-form tech/social.
- **`natural-sentence`** — 4–7 word chunks, sentence case, larger margins. For narrative or documentary.

Word-level timings live in `.words.json`. Group into chunks, convert to output-timeline `.ass` or `.srt`, burn in LAST.

## Which renderer?

Decision: ask the user if they haven't said. Otherwise defer to context.

| Task | Use |
|------|-----|
| Burning captions over talking-head | Remotion |
| B-roll overlay, title cards | Remotion |
| Lower-third, callout, counter | Remotion (has components) |
| Animated chart, kinetic typography | Hyperframes |
| Logo sting, shader transition, intro bumper | Hyperframes |
| Standalone motion-graphics insert | Hyperframes |
| Final composite with base video | Always Remotion or `render.py` |

## Animation spec template (spawn one sub-agent per animation)

Each overlay gets a self-contained brief:

- One-sentence goal
- Absolute output path
- Resolution, fps, codec, CRF, exact duration
- Color palette (hex or design system)
- Font path + index
- Frame-by-frame timeline
- Anti-list: what NOT to include
- Code pattern reference (`video_remotion/src/components/Callout.tsx` or `video_hyperframes/examples/stat-reveal/`)
- Deliverable checklist
- Instruction: "Don't ask questions. If ambiguous, pick the most obvious interpretation."

## Anti-patterns

Persistent failure modes. Don't do these:

- Burning subtitles before overlays
- Single-pass filtergraph with overlays
- Linear animation easing (use `ease_out_cubic` or `ease_in_out_cubic`)
- Hard audio cuts (no fades)
- Re-transcribing cached sources
- Whisper SRT/phrase-level output — throws away sub-second gaps
- Running sub-agents sequentially
- Editing before strategy confirmation
- Assuming video type without examining material first
- Cross-importing Remotion components into Hyperframes or vice versa

## Session memory

After each session, append to `project.md` at the repo root:

```markdown
## Session N — YYYY-MM-DD
**Strategy:** approach summary
**Decisions:** take choices, cuts, grades, animations + rationale
**Reasoning log:** one-line notes on non-obvious choices
**Outstanding:** deferred work
```

## Helper scripts (in `video_pipeline/`)

| Script | Purpose |
|--------|---------|
| `transcribe.py` | Scribe or Whisper transcription; emits `.srt`, `.words.json`, `.segments.json` |
| `pack_transcripts.py` | Phrase-level markdown from cached Scribe JSON |
| `cut_silence.py` | Silence trim based on ffmpeg silencedetect |
| `cut_fillers.py` | Removes filler words using word-level timings |
| `split_reels.py` | Sentence-boundary reel chunks |
| `to_vertical.py` | 9:16 reframe (blur bg or center crop) |
| `render.py` | EDL renderer: extract → fade → concat → overlay → subtitles |

## Entry points

- `studio.py prep <input.mp4>` — transcribe → cut silence → cut fillers → pack
- `studio.py render <edl.json> -o out.mp4` — EDL-driven render
- `cd video_remotion && npm run start` — Remotion studio (browser preview)
- `cd video_hyperframes && npx hyperframes preview` — Hyperframes preview
