---
description: Shape raw long-form footage into a YouTube episode
argument-hint: <video> [--no-cold-open] [--draft]
allowed-tools: Read, Write, Bash(python3:*), Task
---

# Cut $ARGUMENTS into a YouTube episode

## 1. Check the source

```bash
python3 -m reelforge.cli prepare "$1"
```

Reports duration and whether the transcript and signals are warm. On the server
the watcher will normally have done this already.

## 2. Shape the episode

Read `memory/style-profile.md` if it exists, then launch the **producer** agent
with the transcript and signals. It returns the body range, an optional cold
open, drops, chapters, b-roll slots, and metadata — all in source seconds.

Use **producer**, not the reels **editor**. They do opposite jobs: the editor
extracts a moment and discards the rest, the producer keeps everything and
tightens it. Using the wrong one produces a forty-second clip from an hour of
footage, or an hour-long reel.

## 3. Compose and render

```bash
python3 -m reelforge.cli vlog "$1" --episode episode.json [--draft]
```

Writes the EDL, an `.srt` sidecar, a description with chapters, and thumbnail
candidates, then renders.

Captions are **not burned in** for long-form. YouTube has its own caption UI,
viewers may want them off, and burned pixels cannot be auto-translated. The
sidecar `.srt` uploads alongside the video.

## 4. Report

- Runtime before and after, and what came out — chiefly which tangents, and how
  long each was. This is the number they will care about most.
- Whether a cold open was used, and which moment it lifted
- The chapter list as it will appear in the description. **If chapter validation
  failed, say so loudly** — YouTube silently renders none of them when the rules
  are broken, so a quiet failure here means shipping a video with no chapters
  and never noticing.
- B-roll slots, with timecode and prompt, as a shot list to fill
- The top thumbnail candidates and why each scored well
- Title, description, tags

Then say what you would have cut but did not, and why. On a long edit that
judgement is the most useful thing in the report.

## Notes

The EDL is the edit. Change it and re-render; no need to re-analyse.

If the producer returned fewer than three chapters, it should have returned
none — do not pad the list to reach the threshold. A video without chapters is
fine; a video with invented ones is worse.
