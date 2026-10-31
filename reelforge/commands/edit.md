---
description: Hand over a video and get a finished edit back — reels or a YouTube episode, rendered with Remotion
argument-hint: <video> [--mode reels|vlog] [--count N] [--draft]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(reelforge:*), Bash(python3:*), Bash(ffmpeg:*), Bash(ffprobe:*), Task
---

# Edit $ARGUMENTS

Launch the **video-editor** agent with the video path and any options given.
It owns the whole job: transcribe, decide what to keep, compose, render with
Remotion, look at the frames, fix what is wrong. It returns a finished video
in `~/reelforge/outbox/`.

Do not do the edit in the main thread. An hour of transcript is large, and
the agent's context is disposable. It also reviews its own frames before
reporting, which is the step that gets skipped when the edit is rushed.

## Without Claude Code

The same edit runs headless, from a cron job, the inbox watcher, or a phone
over SSH, by calling the Claude API directly:

```bash
reelforge edit <video> --count 3
reelforge edit <video> --mode vlog
```

That needs `ANTHROPIC_API_KEY` in `~/.reelforge/env`. Both paths use the same
editorial prompts (`agents/editor.md`, `agents/producer.md`) and the same
renderer, so their edits do not drift apart.

## Report back

Relay the agent's report: outputs, hooks, what was cut and why, what it
looked at and fixed, anything QC left unresolved, and which engine rendered
it. If the engine was `ffmpeg` rather than `remotion`, say why. The report's
`warnings` field explains it.

Then offer `/reel-feedback`. Anything the user says twice becomes a rule,
and the next edit reflects it.
